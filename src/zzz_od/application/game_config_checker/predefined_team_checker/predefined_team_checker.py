from typing import ClassVar

from cv2.typing import MatLike

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.log_utils import log
from zzz_od.application.game_config_checker.predefined_team_checker import (
    predefined_team_checker_const,
)
from zzz_od.application.zzz_application import ZApplication
from zzz_od.config.team_config import PredefinedTeamInfo
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent
from zzz_od.operation.agent_template_matcher import match_team_agent_template
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.goto.goto_menu import GotoMenu


class TeamWrapper:

    def __init__(self, team_name: str, agent_list: list[Agent]):
        self.team_name: str = team_name
        self.agent_list: list[Agent] = agent_list


class PredefinedTeamChecker(ZApplication):

    TEAM_SCROLL_STEP: int = 6
    TEAM_VISIBLE_COUNT: int = 6
    AGENT_SLOT_RECT_LIST: ClassVar[list[list[Rect]]] = [
        [Rect(172, 225, 354, 412), Rect(365, 225, 547, 412), Rect(558, 225, 740, 412)],
        [Rect(988, 225, 1170, 412), Rect(1181, 225, 1363, 412), Rect(1374, 225, 1556, 412)],
        [Rect(172, 508, 354, 695), Rect(365, 508, 547, 695), Rect(558, 508, 740, 695)],
        [Rect(988, 508, 1170, 695), Rect(1181, 508, 1363, 695), Rect(1374, 508, 1556, 695)],
        [Rect(172, 792, 354, 979), Rect(365, 792, 547, 979), Rect(558, 792, 740, 979)],
        [Rect(988, 792, 1170, 979), Rect(1181, 792, 1363, 979), Rect(1374, 792, 1556, 979)],
    ]

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(
            self,
            ctx=ctx,
            app_id=predefined_team_checker_const.APP_ID,
            op_name=predefined_team_checker_const.APP_NAME,
        )

        self.scroll_times: int = 0  # 下滑次数
        self.checked_team_idx_set: set[int] = set()
        self.checked_agent_signature_set: set[tuple[str, ...]] = set()

    @operation_node(name='前往菜单画面', is_start_node=True)
    def goto_menu(self) -> OperationRoundResult:
        op = GotoMenu(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='前往菜单画面')
    @operation_node(name='前往更多功能画面')
    def goto_menu_more(self) -> OperationRoundResult:
        return self.round_by_goto_screen(screen_name='菜单-更多功能')

    @node_from(from_name='前往更多功能画面')
    @operation_node(name='点击预备编队')
    def click_predefined_team(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='菜单-更多功能', area_name='按钮-预备编队',
                                                 until_not_find_all=[('菜单-更多功能', '按钮-兑换码')],
                                                 success_wait=2, retry_wait=1)

    @node_from(from_name='点击预备编队')
    @operation_node(name='识别编队角色')
    def check_team_members(self) -> OperationRoundResult:
        self.update_team_members(self.last_screenshot)

        if self.scroll_times < 4:
            drag_start = Point(self.ctx.controller.standard_width // 2, self.ctx.controller.standard_height // 2)
            drag_end = drag_start + Point(0, -500)
            self.ctx.controller.drag_to(start=drag_start, end=drag_end)
            self.scroll_times += 1
            return self.round_wait('继续识别', wait=1)
        else:
            return self.round_success()

    def update_team_members(self, screen: MatLike) -> None:
        team_list = self.ctx.team_config.team_list
        visible_start_idx = self._get_visible_start_idx(len(team_list))
        duplicate_prefix_count: int = 0
        has_seen_new_team: bool = False

        # 预备编队固定展示 2 列 3 行。滚动可能重叠，已识别过的三人组合不占用新的配置下标。
        for slot_idx in range(len(self.AGENT_SLOT_RECT_LIST)):
            agent_mr_list = self._match_agent_result_by_slot(screen, slot_idx)
            if len(agent_mr_list) == 0:
                continue

            members = [i.data for i in agent_mr_list]
            agent_signature = tuple(agent.agent_id for agent in members)
            if agent_signature in self.checked_agent_signature_set:
                if not has_seen_new_team:
                    duplicate_prefix_count += 1
                continue

            team_idx = visible_start_idx + slot_idx - duplicate_prefix_count
            if team_idx < 0 or team_idx >= len(team_list):
                continue

            team_info = team_list[team_idx]
            if team_info.idx in self.checked_team_idx_set:
                continue

            team_name = team_info.name

            log.info(f'编队名称: {team_name} 识别代理人: {[i.data.agent_name for i in agent_mr_list]}')

            self._update_team(team_info, team_name, members)
            self.checked_team_idx_set.add(team_info.idx)
            self.checked_agent_signature_set.add(agent_signature)
            has_seen_new_team = True

    def _get_visible_start_idx(self, team_count: int) -> int:
        """
        根据当前滚动次数计算可见编队起始下标。
        """
        max_start_idx = max(0, team_count - self.TEAM_VISIBLE_COUNT)
        return min(self.scroll_times * self.TEAM_SCROLL_STEP, max_start_idx)

    def _match_agent_result_by_slot(self, screen: MatLike, team_slot_idx: int) -> list[MatchResult]:
        """
        按 3 个代理人槽位分别识别，每个槽位只保留最高置信度结果。
        """
        result_list: list[MatchResult] = []
        for agent_rect in self.AGENT_SLOT_RECT_LIST[team_slot_idx]:
            agent_mr_list = match_team_agent_template(self.ctx, screen, agent_rect, None)
            if len(agent_mr_list) == 0:
                continue

            agent_mr = max(agent_mr_list, key=lambda x: x.confidence)
            result_list.append(agent_mr)

        return result_list

    def _update_team(self, team_info: PredefinedTeamInfo, team_name: str, members: list[Agent]) -> None:
        """
        更新编队名称和代理人。
        """
        agent_id_list = [agent.agent_id for agent in members[:3]]
        while len(agent_id_list) < 3:
            agent_id_list.append('unknown')

        new_team_info = PredefinedTeamInfo(
            idx=team_info.idx,
            name=team_name,
            auto_battle=team_info.auto_battle,
            agent_id_list=agent_id_list,
        )
        self.ctx.team_config.update_team(new_team_info)

    @node_from(from_name='识别编队角色')
    @operation_node(name='成功后返回')
    def back_at_last(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op_result(op.execute())


def __debug_update_team_members():
    ctx = ZContext()
    ctx.init()
    from one_dragon.utils import debug_utils
    screen = debug_utils.get_debug_image('497657553-30334c5e-a162-460e-b797-e31e75f7b03b')
    op = PredefinedTeamChecker(ctx)
    op.update_team_members(screen)


def __debug():
    ctx = ZContext()
    ctx.init()
    ctx.run_context.start_running()

    op = PredefinedTeamChecker(ctx)
    op.execute()


if __name__ == '__main__':
    __debug_update_team_members()

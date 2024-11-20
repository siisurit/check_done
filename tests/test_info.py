# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
from check_done.info import (
    PageInfo,
    ProjectV2ItemNode,
    ProjectV2Node,
    ProjectV2SingleSelectFieldNode,
    QueryInfo,
)


def test_can_resolve_nodes():
    fake_nodes = [
        {"__typename": "ProjectV2", "id": "fake_id", "number": 1},
        {
            "__typename": "ProjectV2SingleSelectField",
            "id": "fake_id",
            "name": "fake_name",
            "options": [{"id": "another_fake_id", "name": "another_fake_name"}],
        },
        {"__typename": "ProjectV2Item", "type": "ISSUE", "content": {}, "field_value_by_name": None},
    ]
    fake_page_info = PageInfo(endCursor="a", hasNextPage=False)
    fake_query_info = QueryInfo(nodes=fake_nodes, pageInfo=fake_page_info)

    fake_project_v2_node = fake_query_info.nodes[0]
    assert isinstance(fake_project_v2_node, ProjectV2Node)

    fake_project_v2_single_select_field_node = fake_query_info.nodes[1]
    assert isinstance(fake_project_v2_single_select_field_node, ProjectV2SingleSelectFieldNode)

    fake_project_v2_item_node = fake_query_info.nodes[2]
    assert isinstance(fake_project_v2_item_node, ProjectV2ItemNode)

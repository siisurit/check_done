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
    nodes = [
        {"__typename": "ProjectV2", "id": "fake_id", "number": 1},
        {
            "__typename": "ProjectV2SingleSelectField",
            "id": "fake_id",
            "name": "fake_name",
            "options": [{"id": "another_fake_id", "name": "another_fake_name"}],
        },
        {"__typename": "ProjectV2Item", "type": "ISSUE", "content": {}, "field_value_by_name": None},
    ]
    page_info = PageInfo(endCursor="a", hasNextPage=False)
    query_info = QueryInfo(nodes=nodes, pageInfo=page_info)
    assert isinstance(query_info.nodes[0], ProjectV2Node)
    assert isinstance(query_info.nodes[1], ProjectV2SingleSelectFieldNode)
    assert isinstance(query_info.nodes[2], ProjectV2ItemNode)

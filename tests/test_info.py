from check_done.info import (
    PageInfo,
    PaginatedQueryInfo,
    ProjectV2ItemNodeInfo,
    ProjectV2NodeInfo,
    ProjectV2SingleSelectFieldNodeInfo,
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
    query_info = PaginatedQueryInfo(nodes=nodes, pageInfo=page_info)
    assert isinstance(query_info.nodes[0], ProjectV2NodeInfo)
    assert isinstance(query_info.nodes[1], ProjectV2SingleSelectFieldNodeInfo)
    assert isinstance(query_info.nodes[2], ProjectV2ItemNodeInfo)

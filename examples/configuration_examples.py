#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Yueshu Airbyte Connector 配置示例

本文件展示了如何为 Yueshu 图数据库配置 Airbyte 连接和目标。
"""

import json

# ============================================================================
# 示例 1：简单的电影数据库配置
# ============================================================================

# 1.1 Connection 配置 - 定义如何连接到图数据库
CONNECTION_CONFIG_MOVIE = {
    "hosts": ["192.168.1.100:9669", "192.168.1.101:9669"],
    "user": "root",
    "password": "nebula",
}

# 1.2 Destination 配置 - 定义目标图数据库和写入模式
DESTINATION_CONFIG_MOVIE = {
    "graph": "movie",
    "insert_mode": "insert or replace",  # 选项: insert, insert or replace, insert or ignore, insert or update
}

# 1.3 Catalog 配置 - 定义数据映射（Streams）

# Stream 1: 演员数据
ACTOR_STREAM_CONFIG = {
    "type": "vertex",  # 顶点
    "label": "Actor",  # 在 Schema 中定义的标签
    "primary_key": {
        "source_field": "actor_id",  # 源数据字段
        "dest_field": "id",  # 图中的属性名
    },
    "properties": [
        {
            "source_field": "actor_name",
            "dest_field": "name",
        },
        {
            "source_field": "birth_date",
            "dest_field": "birthDate",
            "transform": "date",  # 转换为日期格式
        },
        {
            "source_field": "height",
            "dest_field": "height",
        },
        {
            "source_field": "nationality",
            "dest_field": "nationality",
        },
    ],
}

# Stream 2: 电影数据
MOVIE_STREAM_CONFIG = {
    "type": "vertex",  # 顶点
    "label": "Movie",
    "primary_key": {
        "source_field": "movie_id",
        "dest_field": "id",
    },
    "properties": [
        {
            "source_field": "movie_title",
            "dest_field": "title",
        },
        {
            "source_field": "release_date",
            "dest_field": "releaseDate",
            "transform": "date",
        },
        {
            "source_field": "runtime",
            "dest_field": "runtime",
        },
        {
            "source_field": "genre",
            "dest_field": "primaryGenre",
        },
    ],
}

# Stream 3: 演员-电影关系（边）
ACTED_IN_STREAM_CONFIG = {
    "type": "edge",  # 边
    "label": "ActedIn",
    "src_vertex": {
        "label": "Actor",
        "primary_key": {
            "source_field": "actor_id",
            "dest_field": "id",
        },
    },
    "dst_vertex": {
        "label": "Movie",
        "primary_key": {
            "source_field": "movie_id",
            "dest_field": "id",
        },
    },
    "multiedge_key": {
        "source_field": "role_id",  # 多边键，用于区分同一对节点之间的多条边
    },
    "properties": [
        {
            "source_field": "character_name",
            "dest_field": "characterName",
        },
        {
            "source_field": "screen_time",
            "dest_field": "screenTime",
        },
    ],
}

# Stream 4: 导演-电影关系（边，无多边键）
DIRECTED_STREAM_CONFIG = {
    "type": "edge",
    "label": "Directed",
    "src_vertex": {
        "label": "Director",
        "primary_key": {
            "source_field": "director_id",
            "dest_field": "id",
        },
    },
    "dst_vertex": {
        "label": "Movie",
        "primary_key": {
            "source_field": "movie_id",
            "dest_field": "id",
        },
    },
    # 注意：没有 multiedge_key，因为导演和电影之间通常只有一条边
    "properties": [
        {
            "source_field": "nominated_for_award",
            "dest_field": "awardNomination",
        },
    ],
}

# ============================================================================
# 示例 2：社交网络图配置
# ============================================================================

CONNECTION_CONFIG_SOCIAL = {
    "hosts": ["localhost:9669"],
    "user": "root",
    "password": "nebula",
}

DESTINATION_CONFIG_SOCIAL = {
    "graph": "social_network",
    "insert_mode": "insert or update",  # 更新现有节点
}

# 用户节点
USER_STREAM_CONFIG = {
    "type": "vertex",
    "label": "User",
    "primary_key": {
        "source_field": "user_id",
        "dest_field": "uid",
    },
    "properties": [
        {
            "source_field": "username",
            "dest_field": "name",
        },
        {
            "source_field": "email",
            "dest_field": "email",
        },
        {
            "source_field": "created_at",
            "dest_field": "joinDate",
            "transform": "date",
        },
        {
            "source_field": "last_login",
            "dest_field": "lastLogin",
            "transform": "datetime",
        },
    ],
}

# 好友关系
FRIENDSHIP_STREAM_CONFIG = {
    "type": "edge",
    "label": "Follows",
    "src_vertex": {
        "label": "User",
        "primary_key": {
            "source_field": "follower_id",
            "dest_field": "uid",
        },
    },
    "dst_vertex": {
        "label": "User",
        "primary_key": {
            "source_field": "followee_id",
            "dest_field": "uid",
        },
    },
    "properties": [
        {
            "source_field": "follow_date",
            "dest_field": "followDate",
            "transform": "date",
        },
    ],
}

# ============================================================================
# 示例 3：生成的 GQL 语句
# ============================================================================

def generate_actor_insert_gql(record):
    """根据记录生成演员插入 GQL"""
    return f"""INSERT (@Actor{{
        id: {record['actor_id']},
        name: "{record['actor_name']}",
        birthDate: date("{record['birth_date']}"),
        height: {record['height']},
        nationality: "{record['nationality']}"
    }})"""


def generate_acted_in_insert_gql(record):
    """根据记录生成演员-电影关系插入 GQL"""
    return f"""MATCH (src@Actor{{id: {record['actor_id']}}), (dst@Movie{{id: {record['movie_id']}})
INSERT (src)-[@ActedIn:{record['role_id']}{{
        characterName: "{record['character_name']}",
        screenTime: {record['screen_time']}
    }}]->(dst)"""


# ============================================================================
# 示例数据
# ============================================================================

SAMPLE_ACTOR_DATA = [
    {
        "actor_id": 1001,
        "actor_name": "Tom Hanks",
        "birth_date": "1956-07-09",
        "height": 183,
        "nationality": "American",
    },
    {
        "actor_id": 1002,
        "actor_name": "Meg Ryan",
        "birth_date": "1961-11-19",
        "height": 171,
        "nationality": "American",
    },
]

SAMPLE_MOVIE_DATA = [
    {
        "movie_id": 2001,
        "movie_title": "Forrest Gump",
        "release_date": "1994-07-06",
        "runtime": 142,
        "genre": "Drama",
    },
    {
        "movie_id": 2002,
        "movie_title": "Sleepless in Seattle",
        "release_date": "1993-06-25",
        "runtime": 105,
        "genre": "Romance",
    },
]

SAMPLE_ACTED_IN_DATA = [
    {
        "actor_id": 1001,
        "movie_id": 2001,
        "role_id": 1,
        "character_name": "Forrest Gump",
        "screen_time": 120,
    },
    {
        "actor_id": 1001,
        "movie_id": 2002,
        "role_id": 1,
        "character_name": "Sam Baldwin",
        "screen_time": 110,
    },
    {
        "actor_id": 1002,
        "movie_id": 2002,
        "role_id": 2,
        "character_name": "Annie Reed",
        "screen_time": 100,
    },
]

SAMPLE_USER_DATA = [
    {
        "user_id": "u001",
        "username": "Alice",
        "email": "alice@example.com",
        "created_at": "2023-01-15",
        "last_login": "2024-01-10 14:30:00",
    },
    {
        "user_id": "u002",
        "username": "Bob",
        "email": "bob@example.com",
        "created_at": "2023-02-20",
        "last_login": "2024-01-09 10:15:00",
    },
]

SAMPLE_FRIENDSHIP_DATA = [
    {
        "follower_id": "u001",
        "followee_id": "u002",
        "follow_date": "2023-03-01",
    },
    {
        "follower_id": "u002",
        "followee_id": "u001",
        "follow_date": "2023-03-05",
    },
]

# ============================================================================
# 打印示例
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Yueshu Airbyte Connector 配置示例")
    print("=" * 80)

    print("\n【示例 1：电影数据库】\n")

    print("Connection 配置:")
    print(json.dumps(CONNECTION_CONFIG_MOVIE, indent=2, ensure_ascii=False))

    print("\nDestination 配置:")
    print(json.dumps(DESTINATION_CONFIG_MOVIE, indent=2, ensure_ascii=False))

    print("\nActor Stream 配置:")
    print(json.dumps(ACTOR_STREAM_CONFIG, indent=2, ensure_ascii=False))

    print("\nActedIn Stream 配置:")
    print(json.dumps(ACTED_IN_STREAM_CONFIG, indent=2, ensure_ascii=False))

    print("\n生成的 GQL 语句示例:")
    for actor_record in SAMPLE_ACTOR_DATA:
        print(generate_actor_insert_gql(actor_record))
        print()

    for acted_in_record in SAMPLE_ACTED_IN_DATA:
        print(generate_acted_in_insert_gql(acted_in_record))
        print()

    print("=" * 80)
    print("【示例 2：社交网络】\n")

    print("Connection 配置:")
    print(json.dumps(CONNECTION_CONFIG_SOCIAL, indent=2, ensure_ascii=False))

    print("\nDestination 配置:")
    print(json.dumps(DESTINATION_CONFIG_SOCIAL, indent=2, ensure_ascii=False))

    print("\nUser Stream 配置:")
    print(json.dumps(USER_STREAM_CONFIG, indent=2, ensure_ascii=False))

    print("\nFollows Stream 配置:")
    print(json.dumps(FRIENDSHIP_STREAM_CONFIG, indent=2, ensure_ascii=False))

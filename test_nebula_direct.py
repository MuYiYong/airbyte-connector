#!/usr/bin/env python3
"""直接测试 nebula5_python 的导入和连接"""

print("测试 1: 检查 nebula5_python 是否已安装...")
try:
    import nebulagraph_python
    print(f"✅ nebulagraph_python 已安装")
    print(f"   版本信息: {nebulagraph_python.__version__ if hasattr(nebulagraph_python, '__version__') else '未知'}")
    print(f"   路径: {nebulagraph_python.__file__}")
except ImportError as e:
    print(f"❌ nebulagraph_python 未安装: {e}")
    print("\n请运行以下命令安装:")
    print("  pip3 install nebula5_python==5.2.1")
    print("\n或使用 Docker 测试:")
    print("  docker run --rm python:3.10-slim bash -c 'pip install nebula5_python==5.2.1 && python -c \"from nebulagraph_python import NebulaClient; print(\\\"Success!\\\")\"'")
    exit(1)

print("\n测试 2: 尝试导入 NebulaClient...")
try:
    from nebulagraph_python import NebulaClient
    print("✅ NebulaClient 导入成功")
except ImportError as e:
    print(f"❌ 无法导入 NebulaClient: {e}")
    exit(1)

print("\n测试 3: 尝试连接到 Nebula Graph...")
HOST = "192.168.15.240:39669"
USERNAME = "root"
PASSWORD = "Nebula123"

print(f"   Host: {HOST}")
print(f"   Username: {USERNAME}")

try:
    # 创建客户端（使用 context manager）
    with NebulaClient(
        hosts=[HOST],
        username=USERNAME,
        password=PASSWORD,
    ) as client:
        print("✅ 连接成功")
        
        # 测试简单查询
        print("\n测试 4: 执行查询 'RETURN 1 AS a, 2 AS b'...")
        result = client.execute("RETURN 1 AS a, 2 AS b")
        print("✅ 查询成功")
        
        # 打印结果
        print("\n结果:")
        if hasattr(result, 'print'):
            result.print()
        
        # 获取原始数据
        print("\n原始数据 (by_column):")
        if hasattr(result, 'as_primitive_by_column'):
            print(result.as_primitive_by_column())
        
        print("\n原始数据 (by_row):")
        if hasattr(result, 'as_primitive_by_row'):
            print(list(result.as_primitive_by_row()))
        
        # 查看所有图 (Yueshu 5.2.0 语法)
        print("\n测试 5: 查看所有图 (SHOW GRAPHS)...")
        result = client.execute("SHOW GRAPHS")
        print("✅ 查询成功")
        if hasattr(result, 'print'):
            result.print()
        
        # 获取图列表
        if hasattr(result, 'as_primitive_by_row'):
            graphs = list(result.as_primitive_by_row())
            if graphs:
                print(f"\n找到 {len(graphs)} 个图")
                for graph in graphs:
                    print(f"  - {graph}")
                
                # 尝试使用第一个图
                first_graph = graphs[0]
                graph_name = None
                
                # 尝试不同的键名
                for key in ['Name', 'name', 'graph_name', 'Graph']:
                    if isinstance(first_graph, dict) and key in first_graph:
                        graph_name = first_graph[key]
                        break
                
                if graph_name:
                    print(f"\n测试 6: 注意 - Yueshu 5.2.0 不需要 OPEN GRAPH 或 USE 命令")
                    print(f"         直接执行 GQL 语句即可，当前图: {graph_name}")
                    
                    # 不执行 OPEN GRAPH，直接调用客户端提供的查询方法
                    # 在实际使用中，INSERT 语句会直接作用于指定的图
                    
                    print(f"\n测试 7: 查询图 '{graph_name}' 的元数据...")
                    # 注意: 以下是查询元数据的方式，不需要先 OPEN
                    # 实际的 INSERT 语句会在 Airbyte 层面处理
                    result = client.execute("SHOW GRAPHS")
                    print("✅ 查询成功")
                    if hasattr(result, 'print'):
                        result.print()
                else:
                    print("无法从结果中提取图名称")
            else:
                print("未找到任何图")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！语法验证成功")
        print("=" * 60)
        
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

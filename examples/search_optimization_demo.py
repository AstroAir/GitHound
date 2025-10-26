"""GitHound搜索引擎性能优化演示

本示例展示如何使用增强的搜索引擎功能获得最佳性能。
"""

import asyncio
from pathlib import Path

from git import Repo

from githound.models import SearchQuery
from githound.search_engine import SearchEngineFactory


async def basic_enhanced_search():
    """基础增强搜索示例"""
    print("=" * 60)
    print("基础增强搜索示例")
    print("=" * 60)

    # 创建增强编排器
    factory = SearchEngineFactory()
    orchestrator = factory.create_orchestrator(
        enhanced=True, enable_caching=True, enable_ranking=True  # 启用所有优化
    )

    # 打开仓库
    repo = Repo(".")
    repo_path = Path(repo.working_dir) if repo.working_dir else Path.cwd()

    # 初始化索引器
    print("\n初始化索引器...")
    orchestrator.initialize_indexer(repo_path)

    # 构建索引（首次运行）
    print("构建索引...")
    stats = await orchestrator.build_index(repo, max_results=1000)
    print(f"索引状态: {stats['status']}")
    print(f"索引提交数: {stats.get('indexed_commits', 0)}")
    print(f"耗时: {stats.get('time_seconds', 0):.2f}秒")

    # 执行搜索
    print("\n执行搜索...")
    query = SearchQuery(content_pattern="search", max_results=10)

    results = []
    async for result in orchestrator.search(repo, query):
        results.append(result)
        print(f"  {result.file_path}: {result.relevance_score:.3f}")

    print(f"\n找到 {len(results)} 个结果")

    # 显示性能报告
    print("\n性能报告:")
    print(orchestrator.get_performance_report())


async def advanced_optimization_demo():
    """高级优化功能演示"""
    print("\n" + "=" * 60)
    print("高级优化功能演示")
    print("=" * 60)

    from githound.search_engine import EnhancedSearchOrchestrator, QueryOptimizer

    # 创建组件
    orchestrator = EnhancedSearchOrchestrator(enable_monitoring=True, enable_optimization=True)

    optimizer = QueryOptimizer()

    # 查询优化演示
    print("\n查询优化演示:")
    queries = [
        SearchQuery(content_pattern="comit mesage"),  # 拼写错误
        SearchQuery(file_path_pattern="src\\utils\\*.py"),  # 路径
        SearchQuery(author_pattern="john"),  # 短查询
    ]

    for original in queries:
        optimized = optimizer.optimize(original)
        print(f"\n原始: {original}")
        print(f"优化: {optimized}")

        # 分析查询
        analysis = optimizer.analyze_query(optimized)
        print(f"复杂度: {analysis['complexity']}")
        if analysis["suggested_optimizations"]:
            print(f"建议: {', '.join(analysis['suggested_optimizations'])}")

    # 性能监控演示
    print("\n\n性能监控演示:")
    repo = Repo(".")

    # 执行多次搜索并监控
    for i in range(3):
        query = SearchQuery(content_pattern=f"test{i}", max_results=5)
        results_count = 0

        async for _ in orchestrator.search(repo, query):
            results_count += 1

        print(f"搜索 {i+1}: 找到 {results_count} 个结果")

    # 获取所有性能分析
    profiles = orchestrator.get_all_profiles()
    print(f"\n总共执行了 {len(profiles)} 次搜索")

    if profiles:
        last_profile = profiles[-1]
        print("\n最后一次搜索详情:")
        print(f"  总时间: {last_profile['total_time_ms']:.2f}ms")
        print("  阶段:")
        for stage in last_profile["stages"]:
            print(
                f"    {stage['name']}: {stage['duration_ms']:.2f}ms ({stage.get('percentage', 0):.1f}%)"
            )

    # 检查瓶颈
    bottlenecks = orchestrator.get_bottlenecks()
    if bottlenecks:
        print(f"\n检测到 {len(bottlenecks)} 个性能问题:")
        for bottleneck in bottlenecks:
            print(f"  [{bottleneck['severity']}] {bottleneck['message']}")
            print(f"    建议: {bottleneck['recommendation']}")


async def indexing_demo():
    """索引系统演示"""
    print("\n" + "=" * 60)
    print("索引系统演示")
    print("=" * 60)

    from githound.search_engine import IncrementalIndexer

    repo = Repo(".")
    repo_path = Path(repo.working_dir) if repo.working_dir else Path.cwd()

    # 创建索引器
    indexer = IncrementalIndexer(repo_path)

    # 尝试加载现有索引
    print("\n加载现有索引...")
    loaded = indexer.load_indexes()
    if loaded:
        print("成功加载现有索引")
    else:
        print("未找到现有索引，将创建新索引")

    # 构建索引
    def progress(message, percent):
        print(f"  {message}: {percent*100:.1f}%")

    print("\n构建索引...")
    stats = indexer.build_incremental_index(repo, progress_callback=progress, max_commits=1000)

    print("\n索引统计:")
    print(f"  状态: {stats['status']}")
    print(f"  索引提交数: {stats['indexed_commits']}")
    print(f"  总提交数: {stats['total_commits']}")
    print(f"  耗时: {stats['time_seconds']:.2f}秒")

    # 使用索引搜索
    print("\n使用索引搜索:")

    # 内容搜索
    content_results = indexer.search_content("search engine", limit=5)
    print(f"\n内容搜索 'search engine': 找到 {len(content_results)} 个结果")
    for commit_hash, score in content_results[:3]:
        print(f"  {commit_hash[:8]}: {score:.3f}")

    # 消息搜索
    message_results = indexer.search_messages("fix bug", limit=5)
    print(f"\n消息搜索 'fix bug': 找到 {len(message_results)} 个结果")
    for commit_hash, score in message_results[:3]:
        print(f"  {commit_hash[:8]}: {score:.3f}")

    # 作者搜索
    author_results = indexer.search_authors("author", limit=5)
    print(f"\n作者搜索 'author': 找到 {len(author_results)} 个结果")
    for commit_hash, score in author_results[:3]:
        print(f"  {commit_hash[:8]}: {score:.3f}")

    # 获取索引统计
    index_stats = indexer.get_stats()
    print("\n索引统计:")
    print(f"  总索引提交数: {index_stats['total_indexed_commits']}")
    print(f"  内容索引词项数: {index_stats['content_index']['total_terms']}")
    print(f"  消息索引词项数: {index_stats['message_index']['total_terms']}")
    print(f"  作者索引词项数: {index_stats['author_index']['total_terms']}")


async def performance_comparison():
    """性能对比演示"""
    print("\n" + "=" * 60)
    print("性能对比演示")
    print("=" * 60)

    import time

    repo = Repo(".")
    query = SearchQuery(content_pattern="search", max_results=20)

    # 标准编排器
    print("\n使用标准编排器...")
    factory = SearchEngineFactory()
    standard_orchestrator = factory.create_orchestrator(enhanced=False)

    start = time.time()
    standard_results = []
    async for result in standard_orchestrator.search(repo, query):
        standard_results.append(result)
    standard_time = time.time() - start

    print(f"  结果数: {len(standard_results)}")
    print(f"  耗时: {standard_time*1000:.2f}ms")

    # 增强编排器
    print("\n使用增强编排器...")
    enhanced_orchestrator = factory.create_orchestrator(enhanced=True)
    repo_path = Path(repo.working_dir) if repo.working_dir else Path.cwd()
    enhanced_orchestrator.initialize_indexer(repo_path)
    await enhanced_orchestrator.build_index(repo)

    start = time.time()
    enhanced_results = []
    async for result in enhanced_orchestrator.search(repo, query):
        enhanced_results.append(result)
    enhanced_time = time.time() - start

    print(f"  结果数: {len(enhanced_results)}")
    print(f"  耗时: {enhanced_time*1000:.2f}ms")

    # 对比
    if enhanced_time > 0:
        speedup = standard_time / enhanced_time
        print(f"\n性能提升: {speedup:.1f}倍")
    else:
        print("\n增强搜索太快，无法准确测量！")


async def main():
    """主函数"""
    print("GitHound 搜索引擎性能优化演示\n")

    # 运行所有演示
    await basic_enhanced_search()
    await advanced_optimization_demo()
    await indexing_demo()
    await performance_comparison()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n查看 OPTIMIZATION_GUIDE.md 获取更多信息")


if __name__ == "__main__":
    asyncio.run(main())

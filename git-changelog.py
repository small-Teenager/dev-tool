import argparse
import git

def get_commit_url(origin_url, commit_hash):
    """根据远程仓库地址生成提交URL"""
    if origin_url.startswith('git@github.com:'):
        # SSH格式GitHub地址
        parts = origin_url.split(':')
        repo_path = parts[1].replace('.git', '')
        return f'https://github.com/{repo_path}/commit/{commit_hash}'
    elif origin_url.startswith('https://github.com/'):
        # HTTPS格式GitHub地址
        if origin_url.endswith('.git'):
            base = origin_url[:-4]
        else:
            base = origin_url
        return f'{base}/commit/{commit_hash}'
    elif origin_url.startswith('git@gitlab.com:'):
        # SSH格式GitLab地址
        parts = origin_url.split(':')
        repo_path = parts[1].replace('.git', '')
        return f'https://gitlab.com/{repo_path}/-/commit/{commit_hash}'
    elif origin_url.startswith('https://gitlab.com/'):
        # HTTPS格式GitLab地址
        if origin_url.endswith('.git'):
            base = origin_url[:-4]
        else:
            base = origin_url
        return f'{base}/-/commit/{commit_hash}'
    else:
        # 其他情况返回短哈希
        return None

def main():
    parser = argparse.ArgumentParser(description='Git提交记录Markdown生成器')
    parser.add_argument('--repo', default='.', help='仓库路径（默认当前目录）')
    parser.add_argument('--branch', default='main', help='目标分支（默认main）')
    parser.add_argument('--since', help='开始日期（格式：YYYY-MM-DD）')
    args = parser.parse_args()

    try:
        repo = git.Repo(args.repo)
    except git.InvalidGitRepositoryError:
        print("错误：指定路径不是有效的Git仓库")
        return

    # 切换到目标分支
    try:
        repo.git.checkout(args.branch)
    except git.exc.GitCommandError as e:
        print(f"分支切换失败：{str(e)}")
        return

    # 获取远程仓库地址
    if repo.remotes:
        origin_url = repo.remotes.origin.url
    else:
        origin_url = None

    # 获取提交记录
    try:
        commits = repo.iter_commits(
            args.branch,
            since=args.since,
            max_count=None  # 获取所有记录
        )
    except Exception as e:
        print(f"获取提交记录失败：{str(e)}")
        return

    # 生成Markdown输出
    print("# Git提交记录\n")
    for commit in commits:
        # 解析提交信息
        short_hash = commit.hexsha[:7]
        commit_time = commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')
        author = '@'+commit.author.name
        message = commit.message.strip().replace('\n', ' ')

        # 生成提交URL
        if origin_url:
            commit_url = get_commit_url(origin_url, short_hash)
            hash_display = f'[{short_hash}]({commit_url})'
        else:
            hash_display = short_hash

        # 生成Markdown行
        print(f"- {message} {hash_display} {author} {commit_time}")

if __name__ == '__main__':
    main()

    # python git-changelog.py --repo /path/to/repo --branch feature-branch --since 2025-01-01

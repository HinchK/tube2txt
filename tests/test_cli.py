from tube2txt import get_parser, normalize_command

def test_parser_aliases():
    parser = get_parser()
    
    # Test 'ls' aliases
    args = parser.parse_args(["ls"])
    assert normalize_command(args.command) == "ls"
    
    args = parser.parse_args(["list"])
    assert normalize_command(args.command) == "ls"

    # Test 'add' aliases
    args = parser.parse_args(["add", "https://youtube.com/watch?v=test"])
    assert normalize_command(args.command) == "add"
    
    args = parser.parse_args(["url", "https://youtube.com/watch?v=test"])
    assert normalize_command(args.command) == "add"
    
    args = parser.parse_args(["process", "https://youtube.com/watch?v=test"])
    assert normalize_command(args.command) == "add"

    # Test 'rm' aliases
    args = parser.parse_args(["rm", "test-slug"])
    assert normalize_command(args.command) == "rm"
    
    args = parser.parse_args(["delete", "test-slug"])
    assert normalize_command(args.command) == "rm"

    # Test 'push' aliases
    args = parser.parse_args(["push", "test-slug"])
    assert normalize_command(args.command) == "push"
    
    args = parser.parse_args(["sync", "test-slug"])
    assert normalize_command(args.command) == "push"

    # Test 'config' aliases
    args = parser.parse_args(["config"])
    assert normalize_command(args.command) == "config"
    
    args = parser.parse_args(["setup"])
    assert normalize_command(args.command) == "config"

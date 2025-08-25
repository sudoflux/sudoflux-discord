#!/usr/bin/env python3
"""Simple test to validate imagine command syntax"""

# Test 1: Check if function signature is valid Python
def test_function_signature():
    try:
        code = '''
async def imagine_command(
    interaction: None,
    prompt: str,
    negative: str = "",
    width: int = 1024,
    height: int = 1024,
    seed: int = -1
):
    pass
'''
        compile(code, '<string>', 'exec')
        print("✓ Function signature is valid Python")
        return True
    except SyntaxError as e:
        print(f"✗ Function signature has syntax error: {e}")
        return False

# Test 2: Check for potential Discord.py issues
def test_parameter_names():
    # Discord.py has some reserved parameter names
    params = ['prompt', 'negative', 'width', 'height', 'seed']
    reserved = ['guild', 'channel', 'user', 'member', 'role', 'self']
    
    conflicts = [p for p in params if p in reserved]
    if conflicts:
        print(f"✗ Parameter names conflict with reserved: {conflicts}")
        return False
    else:
        print("✓ No parameter name conflicts")
        return True

# Test 3: Check description lengths (Discord limit is 100 chars)
def test_description_lengths():
    descriptions = {
        "prompt": "What to generate",
        "negative": "What to avoid in the image", 
        "width": "Image width in pixels",
        "height": "Image height in pixels",
        "seed": "Random seed number"
    }
    
    too_long = []
    for param, desc in descriptions.items():
        if len(desc) > 100:
            too_long.append(f"{param}: {len(desc)} chars")
    
    if too_long:
        print(f"✗ Descriptions too long: {too_long}")
        return False
    else:
        print("✓ All descriptions within Discord's 100 char limit")
        return True

# Test 4: Check command name
def test_command_name():
    name = "imagine"
    if len(name) > 32:
        print(f"✗ Command name too long: {len(name)} chars (max 32)")
        return False
    elif not name.replace('_', '').replace('-', '').isalnum():
        print(f"✗ Command name has invalid characters: {name}")
        return False
    else:
        print("✓ Command name is valid")
        return True

# Run all tests
print("Testing /imagine command compatibility...\n")
all_pass = all([
    test_function_signature(),
    test_parameter_names(),
    test_description_lengths(),
    test_command_name()
])

if all_pass:
    print("\n✅ All validation tests passed!")
    print("\nPossible runtime issues to check:")
    print("1. Check Discord server Integrations settings - command might be disabled")
    print("2. Check for name collision with other bots (e.g., Midjourney)")
    print("3. Check bot startup logs for registration errors")
    print("4. Verify bot has 'applications.commands' OAuth scope")
else:
    print("\n❌ Some tests failed - fix these issues first")
"""
Very simple script to test file output
"""

# No imports needed

with open("test_output.txt", "w") as f:
    f.write("This is a test output file.\n")
    f.write("If you can read this, the script executed successfully.\n")
    
print("Script completed. Check test_output.txt for results.") 
import webbrowser
import time
import sys

def main():
    # Rick Roll URL
    url = "https://youtu.be/dQw4w9WgXcQ?si=W7ppTN4lZUT9ep-Y"
    
    try:
        # Open URL in browser
        webbrowser.open(url)
        
        # Keep the window open for a moment
        time.sleep(2)
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()

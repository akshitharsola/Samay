-- This script will trigger the Apple Events permission dialog for Samay_MacOS
tell application "System Events"
    -- This should trigger the permission dialog
    set processNames to name of every process
    display dialog "Apple Events permission test successful!" & return & "Found " & (count of processNames) & " running processes."
end tell
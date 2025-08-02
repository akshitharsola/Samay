# macOS Shortcuts Setup Guide for Samay AI Services

This guide will help you create macOS Shortcuts for each AI service that Samay can use as an alternative to direct automation.

## Prerequisites

1. **macOS Shortcuts app** (comes pre-installed on macOS 12+)
2. **AI service apps installed**:
   - Claude Desktop
   - Perplexity (Mac app)
   - ChatGPT Desktop
   - Safari (for Gemini)

## Step-by-Step Setup

### 1. Open Shortcuts App

- Press `Cmd + Space` and type "Shortcuts"
- Or find it in Applications folder

### 2. Create Claude Automation Shortcut

1. Click the **"+"** button to create a new shortcut
2. **Name it**: `Samay Claude Automation`
3. **Add actions in this order**:

   #### Step 1: Get Input
   - Search for "**Receive input**" action
   - Set **Input Type**: Text
   - Set **Allow Types**: Text

   #### Step 2: Get JSON Data
   - Search for "**Get Text from Input**" action
   - Connect it to the previous action

   #### Step 3: Parse Query
   - Search for "**Get Value for**" action
   - Set **Get Value for**: `query`
   - Set **Dictionary**: Use output from previous step

   #### Step 4: Open Claude
   - Search for "**Open App**" action
   - Select **Claude** from the list
   - Add **Wait** action: 2 seconds

   #### Step 5: Send Text
   - Search for "**Type Text**" action
   - Connect the query value from Step 3
   - Add **Wait** action: 1 second

   #### Step 6: Submit Query
   - Search for "**Press Key**" action
   - Set Key: **Return** (Enter)
   - Add **Wait** action: 5 seconds

   #### Step 7: Select Response
   - Search for "**Press Key**" action with **Cmd+A** (Select All)
   - Add **Wait** action: 0.5 seconds

   #### Step 8: Copy Response  
   - Search for "**Press Key**" action with **Cmd+C** (Copy)
   - Add **Wait** action: 0.5 seconds

   #### Step 9: Get Response
   - Search for "**Get Clipboard**" action

   #### Step 10: Format Output
   - Search for "**Text**" action
   - Set content to JSON format:
   ```json
   {
     "response": "[Clipboard]",
     "service": "claude",
     "success": true,
     "timestamp": "[Current Date]",
     "metadata": {}
   }
   ```
   - Replace `[Clipboard]` with output from Step 9
   - Replace `[Current Date]` with "Get Current Date" action

4. **Save the shortcut**

### 3. Create Perplexity Automation Shortcut

1. Create new shortcut named: `Samay Perplexity Automation`
2. Follow similar pattern as Claude but adapt for Perplexity:
   - Use **Perplexity** app in "Open App" action
   - Perplexity uses search field, so after typing, press **Enter**
   - Wait longer for search results (7-10 seconds)
   - Select and copy the main response area

### 4. Create ChatGPT Automation Shortcut  

1. Create new shortcut named: `Samay ChatGPT Automation`
2. Adapt for ChatGPT Desktop:
   - Use **ChatGPT** app in "Open App" action  
   - Type query in chat input
   - Press **Enter** or **Cmd+Enter** to submit
   - Wait for response generation (5-15 seconds)
   - Select and copy the latest response

### 5. Create Gemini Automation Shortcut

1. Create new shortcut named: `Samay Gemini Automation`
2. Adapt for Safari + Gemini:
   - Use **Safari** app in "Open App" action
   - Add "**Open URLs**" action with `https://gemini.google.com`
   - Wait for page load (3 seconds)
   - Type query in text input
   - Press **Enter** to submit
   - Wait for response (5-10 seconds)
   - Select and copy response text

## Advanced Configuration

### Adding Error Handling

For each shortcut, you can add error handling:

1. **Add "Try" action** at the beginning
2. **Add "Otherwise" action** for error cases
3. **Return error JSON**:
```json
{
  "response": "Error occurred during automation",
  "service": "service_name", 
  "success": false,
  "timestamp": "[Current Date]",
  "metadata": {"error": "automation_failed"}
}
```

### Optimizing Wait Times

Adjust wait times based on your system performance:
- **Fast systems**: Reduce wait times by 0.5-1 seconds
- **Slower systems**: Increase wait times by 1-2 seconds
- **Network dependent** (Gemini): Add extra wait for web loading

### Testing Your Shortcuts

1. **Test each shortcut individually**:
   - Right-click shortcut → "Run with Input"
   - Provide test JSON: `{"query": "Hello, test message", "service": "claude"}`
   - Verify output format matches expected JSON

2. **Test from Terminal**:
```bash
shortcuts run "Samay Claude Automation" -i test_input.json -o -
```

## Integration with Samay

Once shortcuts are created, the Samay app will automatically detect and use them. You can verify this in the app's debug menu.

## Troubleshooting

### Common Issues:

1. **"Shortcut not found"**
   - Ensure shortcut names match exactly (case-sensitive)
   - Check shortcuts are saved and not in trash

2. **"Automation not working"**
   - Verify apps are installed and accessible
   - Check system permissions for Shortcuts app
   - Test shortcuts manually first

3. **"Invalid JSON output"**
   - Check JSON format in Text action
   - Ensure all placeholders are replaced with actual values
   - Test with online JSON validator

4. **"App not responding"**
   - Increase wait times between actions
   - Ensure apps are not in background/minimized state
   - Check for app updates

### Permissions Required:

- **Accessibility**: May be required for some key press actions
- **Automation**: Allow Shortcuts to control other apps
- **Files**: For reading input JSON files

## Next Steps

After creating all shortcuts:
1. Test each one individually
2. Test through Samay app's "Debug AI Services" feature
3. Adjust timing and error handling as needed
4. Consider creating backup/export of shortcuts

---

**Note**: This approach provides a more reliable alternative to direct UI automation, as it leverages macOS's built-in automation framework while maintaining the same functionality.
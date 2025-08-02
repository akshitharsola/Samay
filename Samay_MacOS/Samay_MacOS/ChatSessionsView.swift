import SwiftUI

struct ChatSessionsView: View {
    @ObservedObject var sessionManager: ChatSessionManager
    @State private var showingNewChatButton = false
    @State private var editingSession: ChatSession?
    @State private var editingTitle = ""
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView
            
            Divider()
            
            // Sessions list
            if sessionManager.chatSessions.isEmpty {
                emptyStateView
            } else {
                sessionsList
            }
        }
        .background(Color(.controlBackgroundColor).opacity(0.3))
        .frame(width: 280)
    }
    
    private var headerView: some View {
        HStack {
            Text("Chat Sessions")
                .font(.headline)
                .foregroundColor(.primary)
            
            Spacer()
            
            Button(action: {
                sessionManager.createNewSession()
            }) {
                Image(systemName: "plus")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.accentColor)
            }
            .buttonStyle(.plain)
            .help("New Chat")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 48))
                .foregroundColor(.secondary.opacity(0.5))
            
            VStack(spacing: 8) {
                Text("No Chat Sessions")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text("Start a new conversation to create your first chat session.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            Button("Start New Chat") {
                sessionManager.createNewSession()
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var sessionsList: some View {
        ScrollView {
            LazyVStack(spacing: 1) {
                ForEach(sessionManager.chatSessions) { session in
                    ChatSessionRowView(
                        session: session,
                        isSelected: session.id == sessionManager.currentSessionId,
                        isEditing: editingSession?.id == session.id,
                        editingTitle: $editingTitle,
                        onSelect: {
                            sessionManager.selectSession(session)
                        },
                        onEdit: {
                            editingSession = session
                            editingTitle = session.title
                        },
                        onSaveEdit: {
                            if !editingTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                                sessionManager.updateSessionTitle(session, title: editingTitle)
                            }
                            editingSession = nil
                            editingTitle = ""
                        },
                        onCancelEdit: {
                            editingSession = nil
                            editingTitle = ""
                        },
                        onDelete: {
                            sessionManager.deleteSession(session)
                        }
                    )
                }
            }
            .padding(.vertical, 8)
        }
    }
}

struct ChatSessionRowView: View {
    let session: ChatSession
    let isSelected: Bool
    let isEditing: Bool
    @Binding var editingTitle: String
    let onSelect: () -> Void
    let onEdit: () -> Void
    let onSaveEdit: () -> Void
    let onCancelEdit: () -> Void
    let onDelete: () -> Void
    
    @State private var isHovered = false
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Session content
            VStack(alignment: .leading, spacing: 4) {
                if isEditing {
                    TextField("Chat title", text: $editingTitle)
                        .textFieldStyle(.plain)
                        .font(.system(size: 14, weight: .medium))
                        .onSubmit {
                            onSaveEdit()
                        }
                } else {
                    Text(session.title)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.primary)
                        .lineLimit(2)
                }
                
                if !session.messages.isEmpty {
                    Text(session.preview)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
                
                HStack {
                    Text("\(session.messageCount) messages")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text(session.lastMessageAt, style: .relative)
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                }
            }
            
            // Action buttons (show on hover or when selected)
            if (isHovered || isSelected) && !isEditing {
                VStack(spacing: 4) {
                    Button(action: onEdit) {
                        Image(systemName: "pencil")
                            .font(.system(size: 10))
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                    .help("Rename")
                    
                    Button(action: onDelete) {
                        Image(systemName: "trash")
                            .font(.system(size: 10))
                            .foregroundColor(.red)
                    }
                    .buttonStyle(.plain)
                    .help("Delete")
                }
            } else if isEditing {
                VStack(spacing: 4) {
                    Button(action: onSaveEdit) {
                        Image(systemName: "checkmark")
                            .font(.system(size: 10))
                            .foregroundColor(.green)
                    }
                    .buttonStyle(.plain)
                    .help("Save")
                    
                    Button(action: onCancelEdit) {
                        Image(systemName: "xmark")
                            .font(.system(size: 10))
                            .foregroundColor(.red)
                    }
                    .buttonStyle(.plain)
                    .help("Cancel")
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(isSelected ? Color.accentColor.opacity(0.15) : Color.clear)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(isSelected ? Color.accentColor.opacity(0.3) : Color.clear, lineWidth: 1)
                )
        )
        .contentShape(Rectangle())
        .onTapGesture {
            if !isEditing {
                onSelect()
            }
        }
        .onHover { hovering in
            isHovered = hovering
        }
        .contextMenu {
            Button("Rename") {
                onEdit()
            }
            
            Button("Delete") {
                onDelete()
            }
            
            Divider()
            
            Button("Export") {
                // TODO: Implement export functionality
            }
        }
    }
}

#Preview {
    let manager = ChatSessionManager()
    return ChatSessionsView(sessionManager: manager)
}
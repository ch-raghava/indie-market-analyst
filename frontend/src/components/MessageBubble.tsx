import { marked } from "marked";
import clsx from "clsx";
import type { ChatMessage } from "../stores/session";
import { ThinkingDrawer } from "./ThinkingDrawer";

type Props = {
  message: ChatMessage;
  streaming: boolean;
  activeTool: string | null;
};

export function MessageBubble({ message, streaming, activeTool }: Props) {
  const isAssistant = message.role === "assistant";
  const html = isAssistant
    ? (marked.parse(message.text || "") as string)
    : null;

  return (
    <div className={clsx("message", message.role)}>
      <div className="role-tag">{message.role}</div>
      {isAssistant && (
        <ThinkingDrawer
          message={message}
          streaming={streaming}
          activeTool={activeTool}
        />
      )}
      {isAssistant ? (
        <div
          className="bubble assistant-bubble"
          dangerouslySetInnerHTML={{ __html: html || "" }}
        />
      ) : (
        <div className="bubble user-bubble">{message.text}</div>
      )}
    </div>
  );
}

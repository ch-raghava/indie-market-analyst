export function ProcessingIndicator({
  streaming,
  activeTool,
}: {
  streaming: boolean;
  activeTool: string | null;
}) {
  if (!streaming) return null;
  return (
    <div className="processing">
      <div className="live-dot" />
      <span>
        {activeTool ? `Running ${activeTool}…` : "Thinking…"}
      </span>
    </div>
  );
}

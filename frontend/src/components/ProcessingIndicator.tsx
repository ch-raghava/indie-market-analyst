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
      <span className="processing-dot" />
      <span className="processing-text">
        {activeTool ? `Running ${activeTool}…` : "Thinking…"}
      </span>
    </div>
  );
}

export function QuickActionRail({ onExport }: { onExport: () => void }) {
  return (
    <div className="quick-action-rail">
      <button onClick={onExport}>Экспорт</button>
    </div>
  );
}

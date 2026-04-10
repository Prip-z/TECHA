export function QuickActionRail({ onExport, exportDisabled = false }: { onExport: () => void; exportDisabled?: boolean }) {
  return (
    <div className="quick-action-rail">
      <button disabled={exportDisabled} onClick={onExport}>
        Экспорт
      </button>
    </div>
  );
}

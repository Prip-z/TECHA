export function LoadingScreen({ label }: { label: string }) {
  return (
    <div className="loading-screen">
      <div className="brand large">
        <span className="brand-copy">
          <strong>Mafia</strong>
          <small>{label}</small>
        </span>
      </div>
    </div>
  );
}

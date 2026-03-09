export default function PropertiesLoading() {
    return (
        <div style={{ paddingTop: 80, minHeight: "100vh" }}>
            <div className="container" style={{ paddingTop: 40 }}>
                <div style={{ height: 32, width: 240, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", marginBottom: 24, animation: "pulse 1.5s ease-in-out infinite" }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 24 }}>
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="glass-card" style={{ overflow: "hidden" }}>
                            <div style={{ height: 220, background: "var(--bg-secondary)", animation: "pulse 1.5s ease-in-out infinite" }} />
                            <div style={{ padding: 20 }}>
                                <div style={{ height: 16, background: "var(--bg-secondary)", borderRadius: 4, marginBottom: 8, width: "70%", animation: "pulse 1.5s ease-in-out infinite" }} />
                                <div style={{ height: 12, background: "var(--bg-secondary)", borderRadius: 4, marginBottom: 8, width: "50%", animation: "pulse 1.5s ease-in-out infinite" }} />
                                <div style={{ height: 20, background: "var(--bg-secondary)", borderRadius: 4, width: "40%", animation: "pulse 1.5s ease-in-out infinite" }} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <style>{`@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.7; } }`}</style>
        </div>
    );
}

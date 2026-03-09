import Nav from "../components/Nav";
import Footer from "../components/Footer";
import Link from "next/link";
import { getCurrentUser, getUserProfile } from "../lib/auth";
import { redirect } from "next/navigation";

export const metadata = { title: "Account — CheapHouse" };

export default async function AccountPage({ searchParams }) {
    const user = await getCurrentUser();
    if (!user) redirect("/login");

    const profile = await getUserProfile(user.id);
    const sp = await searchParams;
    const justSubscribed = sp?.success === "true";

    const isActive = profile?.subscription_status === "active";

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 40, paddingBottom: 80, maxWidth: 640 }}>
                    <h1 style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-display)", marginBottom: 32 }}>
                        My Account
                    </h1>

                    {justSubscribed && (
                        <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid var(--accent-green)", borderRadius: "var(--radius-md)", padding: "16px 20px", marginBottom: 24, fontSize: 14, color: "var(--accent-green)" }}>
                            Welcome to Pro! You now have full access to all features.
                        </div>
                    )}

                    {/* Profile info */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                        <h3 style={{ fontSize: 16, marginBottom: 16 }}>Profile</h3>
                        <div style={{ display: "grid", gap: 12 }}>
                            <div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 2 }}>Email</div>
                                <div style={{ fontSize: 14 }}>{user.email}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 2 }}>Name</div>
                                <div style={{ fontSize: 14 }}>{profile?.display_name || user.user_metadata?.display_name || "Not set"}</div>
                            </div>
                        </div>
                    </div>

                    {/* Subscription */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                        <h3 style={{ fontSize: 16, marginBottom: 16 }}>Subscription</h3>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                            <span className={`badge ${isActive ? "badge-green" : "badge-amber"}`}>
                                {isActive ? "Pro" : "Free"}
                            </span>
                            <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                                {isActive ? "Full access to all features" : "Limited access"}
                            </span>
                        </div>
                        {isActive ? (
                            <form action="/api/stripe/portal" method="POST">
                                <button type="submit" className="btn btn-secondary" style={{ padding: "10px 20px" }}>
                                    Manage Subscription
                                </button>
                            </form>
                        ) : (
                            <Link href="/pricing" className="btn btn-primary" style={{ padding: "10px 20px", display: "inline-block" }}>
                                Upgrade to Pro
                            </Link>
                        )}
                    </div>

                    {/* Quiz */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                        <h3 style={{ fontSize: 16, marginBottom: 16 }}>Property Preferences</h3>
                        {profile?.quiz_answers ? (
                            <>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
                                    {Object.entries(profile.quiz_answers).map(([key, val]) => (
                                        <div key={key} style={{ fontSize: 13 }}>
                                            <span style={{ color: "var(--text-muted)", textTransform: "capitalize" }}>{key.replace("_", " ")}: </span>
                                            <span style={{ color: "var(--text-secondary)" }}>{String(val).replace(/-/g, " ")}</span>
                                        </div>
                                    ))}
                                </div>
                                <Link href="/quiz" style={{ fontSize: 13, color: "var(--accent-blue)" }}>Retake Quiz →</Link>
                            </>
                        ) : (
                            <div>
                                <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
                                    Take our quiz to get personalized property matches.
                                </p>
                                <Link href="/quiz" className="btn btn-secondary" style={{ padding: "8px 16px", fontSize: 13 }}>
                                    Take Quiz
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* Quick links */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <Link href="/saved" className="glass-card" style={{ padding: 20, textAlign: "center", textDecoration: "none", color: "inherit" }}>
                            <div style={{ fontSize: 24, marginBottom: 8 }}>♡</div>
                            <div style={{ fontSize: 14 }}>Saved Properties</div>
                        </Link>
                        <Link href="/properties" className="glass-card" style={{ padding: 20, textAlign: "center", textDecoration: "none", color: "inherit" }}>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-secondary)", marginBottom: 8 }}>Browse</div>
                            <div style={{ fontSize: 14 }}>Browse Properties</div>
                        </Link>
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
}

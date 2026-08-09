import Nav from "../components/Nav";
import Footer from "../components/Footer";
import VerificationForm from "./VerificationForm";

export const metadata = {
    title: "Check a Japanese Property Listing — CheapHouse",
    description: "Request a 48-hour availability and evidence check for a Japanese property listing.",
};

export default async function VerifyPage({ searchParams }) {
    const params = await searchParams;
    const defaultUrl = typeof params?.url === "string" ? params.url : "";

    return (
        <>
            <Nav />
            <main className="page-shell">
                <div className="container verify-layout">
                    <section className="verify-copy">
                        <div className="eyebrow">48-hour property check</div>
                        <h1>Send the listing.<br />Get the truth layer.</h1>
                        <p>
                            We check the original source, buyer constraints, visible cost signals,
                            risk evidence, and the questions that still require a local professional.
                        </p>
                        <div className="offer-price">$149 <span>per property · founding beta</span></div>
                        <ul className="deliverable-list">
                            <li>Current availability and source proof</li>
                            <li>Attractive, unclear, risky, and verify sections</li>
                            <li>Visible purchase and renovation cost exposure</li>
                            <li>Clear unknowns, never filled with guesses</li>
                        </ul>
                        <p className="offer-note">No subscription. You only pay after we confirm the listing can be checked.</p>
                    </section>
                    <VerificationForm defaultUrl={defaultUrl} />
                </div>
            </main>
            <Footer />
        </>
    );
}


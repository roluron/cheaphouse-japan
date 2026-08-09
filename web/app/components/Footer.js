import Link from "next/link";

export default function Footer() {
    return (
        <footer className="footer">
            <div className="container footer-simple">
                <div>
                    <div className="footer-brand">CheapHouse Japan</div>
                    <p>Availability first. Evidence before certainty.</p>
                </div>
                <div className="footer-links">
                    <Link href="/properties">Verified listings</Link>
                    <Link href="/verify">Check a listing</Link>
                </div>
                <p>&copy; {new Date().getFullYear()} CheapHouse</p>
            </div>
        </footer>
    );
}

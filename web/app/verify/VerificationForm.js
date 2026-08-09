"use client";

import { useState } from "react";

export default function VerificationForm({ defaultUrl = "" }) {
    const [status, setStatus] = useState("idle");
    const [message, setMessage] = useState("");

    async function handleSubmit(event) {
        event.preventDefault();
        const formElement = event.currentTarget;
        setStatus("submitting");
        setMessage("");

        const form = new FormData(formElement);
        const response = await fetch("/api/verification-request", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(Object.fromEntries(form.entries())),
        });
        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            setStatus("error");
            setMessage(result.error || "The request could not be sent. Please try again.");
            return;
        }

        setStatus("success");
        setMessage("Request received. We will confirm within one business day whether the listing can be verified.");
        formElement.reset();
    }

    return (
        <form className="verification-form glass-card" onSubmit={handleSubmit}>
            <h2>Request a check</h2>
            <label>
                Japanese listing URL
                <input name="listing_url" type="url" defaultValue={defaultUrl} placeholder="https://..." required />
            </label>
            <label>
                Your email
                <input name="email" type="email" placeholder="you@example.com" required />
            </label>
            <label>
                What are you considering it for?
                <select name="buyer_goal" defaultValue="home">
                    <option value="home">Home or second home</option>
                    <option value="renovation">Renovation project</option>
                    <option value="rental">Rental or hospitality</option>
                    <option value="unknown">Still exploring</option>
                </select>
            </label>
            <label>
                Anything we should know? <span>Optional</span>
                <textarea name="notes" rows="4" maxLength="2000" placeholder="Timing, budget, location constraints..." />
            </label>
            <button className="btn btn-primary btn-lg" type="submit" disabled={status === "submitting"}>
                {status === "submitting" ? "Sending..." : "Request verification"}
            </button>
            {message && <p className={`form-message form-${status}`} role="status">{message}</p>}
            <p className="form-privacy">No card required now. We use these details only to evaluate and deliver your request.</p>
        </form>
    );
}

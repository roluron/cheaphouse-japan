export const VERIFICATION_WINDOW_HOURS = 72;

export function getVerifiedCutoff(now = new Date()) {
    return new Date(now.getTime() - VERIFICATION_WINDOW_HOURS * 60 * 60 * 1000).toISOString();
}

export function getAvailability(property, now = new Date()) {
    const status = property?.listing_status;
    const checkedAt = property?.last_checked_at || property?.status_checked_at;

    if (status === "sold") {
        return { key: "sold", label: "Sold", detail: "The source indicates this property is sold.", tone: "rose" };
    }

    if (status === "removed") {
        return { key: "removed", label: "Listing removed", detail: "The original source page is no longer available.", tone: "rose" };
    }

    if (status !== "active") {
        return { key: "uncertain", label: "Availability unconfirmed", detail: "We could not confirm that this listing is currently active.", tone: "amber" };
    }

    const checkedDate = checkedAt ? new Date(checkedAt) : null;
    if (!checkedDate || Number.isNaN(checkedDate.getTime())) {
        return { key: "uncertain", label: "Availability unconfirmed", detail: "No reliable source check is recorded.", tone: "amber" };
    }

    const ageHours = Math.max(0, (now.getTime() - checkedDate.getTime()) / 3_600_000);
    if (ageHours > VERIFICATION_WINDOW_HOURS) {
        return { key: "stale", label: "Verification expired", detail: "This source has not been checked in the last 72 hours.", tone: "amber", checkedAt };
    }

    const ageLabel = ageHours < 1 ? "less than an hour ago" : `${Math.floor(ageHours)}h ago`;
    return { key: "verified", label: "Verified active", detail: `Source checked ${ageLabel}.`, tone: "green", checkedAt };
}


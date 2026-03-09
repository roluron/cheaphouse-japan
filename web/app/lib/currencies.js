const RATES = {
    JPY: 1, USD: 0.0067, EUR: 0.0061, GBP: 0.0053, CNY: 0.048,
    VND: 168, AUD: 0.0103, NZD: 0.0113, CAD: 0.0094, SGD: 0.009,
    THB: 0.23, KRW: 9.2,
};

export function convertPrice(priceJpy, currency) {
    return Math.round(priceJpy * (RATES[currency] || 1));
}

export function formatCurrency(amount, currency) {
    try {
        return new Intl.NumberFormat("en-US", {
            style: "currency", currency, maximumFractionDigits: 0,
        }).format(amount);
    } catch {
        return `${currency} ${amount.toLocaleString()}`;
    }
}

export const SUPPORTED_CURRENCIES = Object.keys(RATES);

export function formatPriceMulti(priceJpy, currency) {
    if (!priceJpy) return "Price TBD";
    const jpyStr = `¥${priceJpy.toLocaleString()}`;
    if (!currency || currency === "JPY") return jpyStr;
    const converted = convertPrice(priceJpy, currency);
    return `${jpyStr} (${formatCurrency(converted, currency)})`;
}

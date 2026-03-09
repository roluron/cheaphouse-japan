export const COUNTRIES = [
    { code: "jp", name: "Japan", flag: "JP", status: "active", currency: "JPY", tagline: "Akiya, countryside retreats, and affordable homes" },
    { code: "fr", name: "France", flag: "FR", status: "coming_soon", currency: "EUR", tagline: "Village houses, countryside chateaux, and Mediterranean gems" },
    { code: "vn", name: "Vietnam", flag: "VN", status: "coming_soon", currency: "VND", tagline: "Tropical homes, beach properties, and heritage houses" },
    { code: "pt", name: "Portugal", flag: "PT", status: "coming_soon", currency: "EUR", tagline: "Algarve coast, Lisbon apartments, and rural quintas" },
    { code: "it", name: "Italy", flag: "IT", status: "coming_soon", currency: "EUR", tagline: "Tuscan farmhouses, Sicilian villas, and village homes" },
    { code: "es", name: "Spain", flag: "ES", status: "coming_soon", currency: "EUR", tagline: "Pueblo houses, coastal apartments, and rural fincas" },
    { code: "gr", name: "Greece", flag: "GR", status: "coming_soon", currency: "EUR", tagline: "Island homes, village houses, and Aegean retreats" },
    { code: "nz", name: "New Zealand", flag: "NZ", status: "coming_soon", currency: "NZD", tagline: "Remote cottages, farm stays, and coastal properties" },
    { code: "au", name: "Australia", flag: "AU", status: "coming_soon", currency: "AUD", tagline: "Outback homes, coastal retreats, and bush properties" },
    { code: "us", name: "USA", flag: "US", status: "coming_soon", currency: "USD", tagline: "Detroit bargains, rural homesteads, and fixer-uppers" },
];

export function getActiveCountries() {
    return COUNTRIES.filter(c => c.status === "active");
}

export function getComingSoonCountries() {
    return COUNTRIES.filter(c => c.status === "coming_soon");
}

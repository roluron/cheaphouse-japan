export default function robots() {
    return {
        rules: [
            { userAgent: "*", allow: "/", disallow: ["/admin", "/api", "/auth"] },
        ],
        sitemap: "https://cheaphouse.app/sitemap.xml",
    };
}

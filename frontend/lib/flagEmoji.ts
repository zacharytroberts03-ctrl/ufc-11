// Country name → ISO 3166-1 alpha-2 code → emoji flag.
// Covers the realistic UFC fighter base. Add entries as they show up.

const COUNTRY_TO_CODE: Record<string, string> = {
  // North America
  "United States": "US", "USA": "US", "U.S.A.": "US", "America": "US",
  "Canada": "CA",
  "Mexico": "MX",
  "Cuba": "CU", "Dominican Republic": "DO", "Puerto Rico": "PR", "Jamaica": "JM",
  "Haiti": "HT", "Trinidad and Tobago": "TT", "Bahamas": "BS",

  // South America
  "Brazil": "BR",
  "Argentina": "AR",
  "Chile": "CL",
  "Peru": "PE",
  "Colombia": "CO",
  "Venezuela": "VE",
  "Ecuador": "EC",
  "Bolivia": "BO",
  "Paraguay": "PY",
  "Uruguay": "UY",
  "Suriname": "SR",
  "Guyana": "GY",

  // Europe — UK & Ireland
  "United Kingdom": "GB", "UK": "GB", "Great Britain": "GB",
  "England": "GB", "Scotland": "GB", "Wales": "GB", "Northern Ireland": "GB",
  "Ireland": "IE",

  // Europe — West / Central
  "France": "FR", "Germany": "DE", "Spain": "ES", "Portugal": "PT",
  "Italy": "IT", "Netherlands": "NL", "Belgium": "BE", "Switzerland": "CH",
  "Austria": "AT", "Luxembourg": "LU",

  // Europe — Nordic
  "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI",
  "Iceland": "IS",

  // Europe — Eastern
  "Russia": "RU", "Russian Federation": "RU",
  "Ukraine": "UA", "Belarus": "BY",
  "Poland": "PL", "Czech Republic": "CZ", "Czechia": "CZ", "Slovakia": "SK",
  "Hungary": "HU", "Romania": "RO", "Bulgaria": "BG", "Moldova": "MD",
  "Lithuania": "LT", "Latvia": "LV", "Estonia": "EE",
  "Croatia": "HR", "Slovenia": "SI", "Serbia": "RS", "Bosnia and Herzegovina": "BA",
  "Albania": "AL", "North Macedonia": "MK", "Kosovo": "XK", "Montenegro": "ME",
  "Greece": "GR", "Cyprus": "CY", "Malta": "MT",

  // Caucasus / Central Asia
  "Georgia": "GE", "Armenia": "AM", "Azerbaijan": "AZ",
  "Kazakhstan": "KZ", "Kyrgyzstan": "KG", "Uzbekistan": "UZ",
  "Tajikistan": "TJ", "Turkmenistan": "TM",

  // Middle East / North Africa
  "Turkey": "TR",
  "Iran": "IR", "Iraq": "IQ", "Israel": "IL", "Palestine": "PS",
  "Saudi Arabia": "SA", "United Arab Emirates": "AE", "UAE": "AE",
  "Qatar": "QA", "Kuwait": "KW", "Bahrain": "BH", "Oman": "OM",
  "Jordan": "JO", "Lebanon": "LB", "Syria": "SY", "Yemen": "YE",
  "Egypt": "EG", "Morocco": "MA", "Algeria": "DZ", "Tunisia": "TN",
  "Libya": "LY", "Sudan": "SD",

  // Sub-Saharan Africa
  "Nigeria": "NG", "Cameroon": "CM", "Senegal": "SN",
  "Côte d'Ivoire": "CI", "Ivory Coast": "CI", "Ghana": "GH", "Kenya": "KE",
  "South Africa": "ZA", "Ethiopia": "ET", "Tanzania": "TZ", "Uganda": "UG",
  "Zimbabwe": "ZW", "Zambia": "ZM",
  "Democratic Republic of the Congo": "CD", "DRC": "CD",
  "Republic of the Congo": "CG",
  "Mali": "ML", "Burkina Faso": "BF", "Niger": "NE",

  // Asia
  "Japan": "JP",
  "South Korea": "KR", "Korea": "KR", "North Korea": "KP",
  "China": "CN", "Taiwan": "TW", "Hong Kong": "HK", "Macau": "MO",
  "Mongolia": "MN",
  "Vietnam": "VN", "Thailand": "TH", "Cambodia": "KH", "Laos": "LA",
  "Myanmar": "MM", "Burma": "MM",
  "Philippines": "PH", "Indonesia": "ID", "Malaysia": "MY", "Singapore": "SG",
  "Brunei": "BN", "Timor-Leste": "TL",
  "India": "IN", "Pakistan": "PK", "Bangladesh": "BD", "Sri Lanka": "LK",
  "Nepal": "NP", "Bhutan": "BT", "Maldives": "MV", "Afghanistan": "AF",

  // Oceania
  "Australia": "AU", "New Zealand": "NZ",
  "Papua New Guinea": "PG", "Fiji": "FJ", "Samoa": "WS", "Tonga": "TO",
};

export function flagEmojiFromCountry(country: string | undefined | null): string | null {
  if (!country) return null;
  const trimmed = country.trim();
  if (!trimmed) return null;
  const code = COUNTRY_TO_CODE[trimmed];
  if (!code) return null;
  // Convert ISO 3166-1 alpha-2 code to regional indicator symbols.
  const codePoints = code
    .toUpperCase()
    .split("")
    .map((c) => 127397 + c.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

// US-state fallback: Tapology often writes "Las Vegas, Nevada" without
// trailing country, so a state name should still resolve to the US flag.
const US_STATES = new Set([
  "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
  "Delaware","Florida","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas",
  "Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
  "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
  "New Hampshire","New Jersey","New Mexico","New York","North Carolina",
  "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
  "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
  "Virginia","Washington","West Virginia","Wisconsin","Wyoming",
  "District of Columbia","D.C."
  // Georgia is intentionally NOT in this set — the country map's "Georgia → GE"
  // wins. American fighters from the state will normally have "United States"
  // as the trailing segment in their location.
]);

// "Las Vegas, Nevada, United States" → "United States"
// "Dubai, United Arab Emirates" → "United Arab Emirates"
// "Naha, Okinawa, Japan" → "Japan"
// "Las Vegas, Nevada" → "United States" (US-state fallback)
export function countryFromLocation(location: string | undefined | null): string | null {
  if (!location) return null;
  const parts = location
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  if (!parts.length) return null;
  const last = parts[parts.length - 1];
  if (last in COUNTRY_TO_CODE) return last;
  if (US_STATES.has(last)) return "United States";
  // Walk backward in case the last segment is a city (e.g., trailing whitespace
  // weirdness) but a country is one segment back.
  for (let i = parts.length - 2; i >= 0; i--) {
    if (parts[i] in COUNTRY_TO_CODE) return parts[i];
    if (US_STATES.has(parts[i])) return "United States";
  }
  return last;
}

export function flagEmojiFromLocation(location: string | undefined | null): string | null {
  return flagEmojiFromCountry(countryFromLocation(location));
}

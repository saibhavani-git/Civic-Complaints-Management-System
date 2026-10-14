export function validatePhoneInput(phone: string): string | null {
  const trimmed = phone.trim();
  if (!trimmed) return "Phone number is required";
  const digits = trimmed.replace(/\D/g, "");
  if (digits.length < 10 || digits.length > 15) {
    return "Enter a valid phone number (10–15 digits)";
  }
  return null;
}

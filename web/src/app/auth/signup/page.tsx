import { Metadata } from "next"
import { SignupBox } from "@/components/signup-box"

export const metadata: Metadata = {
  title: "Sign Up",
  description: "Sign up for an account using the form below.",
}

export default function SignupPage() {
  return <SignupBox />
}
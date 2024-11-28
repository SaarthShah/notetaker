import { Metadata } from "next"
import { LoginBox } from "@/components/login-box"

export const metadata: Metadata = {
  title: "Authentication",
  description: "Authentication forms built using the components.",
}

export default function AuthenticationPage() {
  return <LoginBox />
}
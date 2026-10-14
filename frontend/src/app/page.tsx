"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Shield, Brain, MapPin, BarChart3, Clock, CheckCircle2, ArrowRight } from "lucide-react";

const features = [
  { icon: Brain, title: "AI Classification", desc: "Complaints auto-routed to the right department" },
  { icon: Clock, title: "Real-time Tracking", desc: "Follow your complaint status at every step" },
  { icon: MapPin, title: "Location-based", desc: "Pin issues on a map for precise resolution" },
  { icon: BarChart3, title: "Analytics", desc: "Data-driven insights for authorities" },
  { icon: CheckCircle2, title: "Faster Resolution", desc: "Smart prioritization reduces response time" },
  { icon: Shield, title: "Secure & Transparent", desc: "Your data is protected end-to-end" },
];

const steps = [
  { num: "01", title: "Report", desc: "Submit your issue with photos and location" },
  { num: "02", title: "AI Processing", desc: "System classifies and assigns priority" },
  { num: "03", title: "Resolution", desc: "Officer resolves and you get notified" },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden border-b bg-white">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50 via-background to-background" />
        <div className="page-container relative py-20 sm:py-28 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary mb-6">
            <Brain className="h-4 w-4" />
            AI-Powered E-Governance
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-foreground max-w-3xl mx-auto leading-tight">
            Report civic issues.<br />
            <span className="text-primary">Get them resolved faster.</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
            A smart grievance portal that uses AI to classify, prioritize, and route your complaints to the right department.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/sign-in">
              <Button size="lg" className="w-full sm:w-auto gap-2">
                Sign in <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">
                Log in
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="page-container py-16">
        <h2 className="text-center section-title mb-2">How it works</h2>
        <p className="text-center section-subtitle mb-10">Three simple steps to resolve your issue</p>
        <div className="grid md:grid-cols-3 gap-6">
          {steps.map(({ num, title, desc }) => (
            <div key={num} className="relative rounded-xl border bg-card p-6 text-center">
              <span className="text-3xl font-bold text-primary/20">{num}</span>
              <h3 className="mt-2 font-semibold">{title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="border-t bg-white py-16">
        <div className="page-container">
          <h2 className="text-center section-title mb-2">Platform features</h2>
          <p className="text-center section-subtitle mb-10">Built for citizens and government alike</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-xl border bg-card p-5 hover:shadow-sm transition-shadow">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 mb-3">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-1 text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

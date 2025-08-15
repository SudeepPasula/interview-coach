"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Mock() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the new dashboard
    router.replace("/");
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Redirecting to Interview Coach...
        </h1>
        <p className="text-gray-600">
          The new dashboard is now available at the home page.
        </p>
      </div>
    </div>
  );
}

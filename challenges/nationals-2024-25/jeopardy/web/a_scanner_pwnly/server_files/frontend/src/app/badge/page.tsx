"use client";

import { Fragment, useState } from "react";
import * as api from "@/lib/api";

export default function BadgePage() {
  const [badgeUrl, setBadgeUrl] = useState<string | null>(null);

  async function createBadge() {
    const qrCode = await api.createBadge();
    setBadgeUrl(qrCode.image_url);
  }

  function renderBadgeUrl() {
    if (!badgeUrl) {
      return <></>;
    }

    return (
      <div>
        <img src={badgeUrl} height={400} width={400} />
        <p>Show this badge when you are at the polls!</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Election Badge Creation Center</h1>
      {renderBadgeUrl()}
      <button onClick={createBadge} className="button">
        Get Your Badge
      </button>
    </div>
  );
}

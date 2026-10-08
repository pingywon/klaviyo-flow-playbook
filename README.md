# Flow Playbook

The emails an online store sends on its own, and what each one is for.

**See it as a map: https://pingywon.github.io/klaviyo-flow-playbook/**

These are the automated email flows from a working Klaviyo account, rewritten to fit any shop. The store's name, products, addresses, codes and account IDs are gone. The structure is kept: what starts each flow, how long it waits, who it skips, and what each email has to do.

Current version: <!-- version -->v1.0.1<!-- /version -->

## The flows

<!-- flows -->
| Flow | What it is for | Status | File |
|---|---|---|---|
| Welcome series | Turns a new subscriber into a first-time buyer. | Running | [01-welcome-series.json](flows/core/01-welcome-series.json) |
| Browse abandonment | Brings back someone who looked and left. | Running | [02-browse-abandonment.json](flows/core/02-browse-abandonment.json) |
| Abandoned cart | Recovers a checkout that was started, not finished. | Running | [03-abandoned-cart.json](flows/core/03-abandoned-cart.json) |
| Price drop alert | Says when something they looked at got cheaper. | Running | [04-price-drop-alert.json](flows/core/04-price-drop-alert.json) |
| Back in stock | Tells people a sold-out item has returned. | Running | [05-back-in-stock.json](flows/core/05-back-in-stock.json) |
| Waitlist alert | Tells the owner what shoppers are waiting for. | Running | [06-waitlist-alert.json](flows/core/06-waitlist-alert.json) |
| Owner's guide series | Teaches new customers to use what they bought. | Running | [07-owners-guide-series.json](flows/core/07-owners-guide-series.json) |
| Review request | Asks for a review after real use. | Built, not switched on | [08-review-request.json](flows/core/08-review-request.json) |
| Accessory cross-sell | Offers the add-on a new purchase needs. | Built, not switched on | [09-accessory-cross-sell.json](flows/core/09-accessory-cross-sell.json) |
| Reorder reminder | Prompts a replacement before the old one wears out. | Built, not switched on | [10-reorder-reminder.json](flows/core/10-reorder-reminder.json) |
| Win-back | Invites lapsed customers back before they forget. | Running | [11-win-back.json](flows/core/11-win-back.json) |

Planned, in the order they become worth building:

| When | Flow | What it is for | File |
|---|---|---|---|
| Next | Add-to-cart reminder | Catches shoppers who add to cart but never reach checkout. | [01-add-to-cart-reminder.json](flows/planned/01-add-to-cart-reminder.json) |
| Next | Delivery-timed guide | Starts the how-to emails when the parcel actually arrives. | [02-delivery-timed-guide.json](flows/planned/02-delivery-timed-guide.json) |
| Next | Second-order nudge | Earns the second order, the hardest one to get. | [03-second-order-nudge.json](flows/planned/03-second-order-nudge.json) |
| Next | Welcome branch for buyers | Stops offering a first-order code to people who already ordered. | [04-welcome-branch-for-buyers.json](flows/planned/04-welcome-branch-for-buyers.json) |
| Next | Sunset | Stops emailing people who no longer open. | [05-sunset.json](flows/planned/05-sunset.json) |
| Next | Low-stock alert | Warns interested shoppers when an item is nearly gone. | [06-low-stock-alert.json](flows/planned/06-low-stock-alert.json) |
| Next | Refund follow-up | Turns a refund into feedback. | [07-refund-follow-up.json](flows/planned/07-refund-follow-up.json) |
| Then | VIP thank-you | Rewards the best customers before they ask. | [08-vip-thank-you.json](flows/planned/08-vip-thank-you.json) |
| Then | Purchase anniversary | Marks a year since the first order. | [09-purchase-anniversary.json](flows/planned/09-purchase-anniversary.json) |
| Then | Cross-sell by category | Recommends the right next product for what was just bought. | [10-cross-sell-by-category.json](flows/planned/10-cross-sell-by-category.json) |
| Then | Smarter cart branches | Treats big carts and returning customers differently. | [11-smarter-cart-branches.json](flows/planned/11-smarter-cart-branches.json) |
| Then | Review to referral | Asks happy reviewers to bring a friend. | [12-review-to-referral.json](flows/planned/12-review-to-referral.json) |
| Later | Text-message steps | Adds a text where minutes matter. | [13-text-message-steps.json](flows/planned/13-text-message-steps.json) |
| Later | Predicted reorder | Reminds each customer near the date they are likely to reorder. | [14-predicted-reorder.json](flows/planned/14-predicted-reorder.json) |
| Later | Churn-risk save | Reaches customers who are drifting, before they lapse. | [15-churn-risk-save.json](flows/planned/15-churn-risk-save.json) |
| Later | Alerts to team chat | Sends owner alerts to chat or a helpdesk instead of an inbox. | [16-alerts-to-team-chat.json](flows/planned/16-alerts-to-team-chat.json) |
| Later | Standing A/B tests | Keeps one test running on the busiest flows. | [17-standing-ab-tests.json](flows/planned/17-standing-ab-tests.json) |
<!-- /flows -->

## How to use one

1. Open a file in `flows/core/`.
2. In Klaviyo, create a flow with the same trigger.
3. Add the steps in order: waits, emails, splits.
4. Copy the rules into the flow's filters.
5. Write each email to do its one job. The example subject is only a starting point.

## What is in a flow file

| Field | Meaning |
|---|---|
| `purpose` | What the flow is for, in one line |
| `trigger` | What starts it |
| `steps` | What happens, in order: `wait`, `wait-for`, `email`, `alert`, `text`, `webhook`, `split`, `note` |
| `rules` | Who gets in and who is skipped |
| `why` | Why it is built this way |
| `watch` | What goes wrong if you are not careful |
| `needs` | Planned flows only: what must be in place first |

## Rebuild the page

```
python3 tools/build_site.py
python3 -m unittest discover -s tests
```

The page (`docs/index.html`) and the tables above are generated from the flow files. The version number comes from `VERSION`. The tab icon is drawn by `tools/make_icons.py`, which needs Pillow.

An independent project. Not affiliated with or endorsed by Klaviyo. Typeface credit is in `CREDITS.md`.

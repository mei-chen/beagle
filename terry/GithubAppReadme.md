Here's the App for `dev` - https://github.com/apps/snoopyweb-dev

For now it works like this:
1. User installs App, gives permissions and is redirected back to github.
2. Upon install we create new User object without password but with github_access_token.
3. Now after each commit in pull request, we get a webhook call and start project analysis (for latest version of pull request's branch). Until process is completed, user's pull request gets a `pending` state label from our App.
4. After analysis is completed pending state changes into either:
- success (green report status)
- failure (yellow report status)
- error (red report status)
5. If user uninstalls App, user becomes `inactive` but still dwells in db.

---

What we can do but we don't do (at least yet):
1. App is not listed in https://github.com/marketplace
This requires github team's review of our app and we don't want dev version to be reviewed (at least I think so).
2. Check for user subscription (if we put our App to Marketplace, there is Plans & Pricing there, so I think we do not need to restrict private repos on our side).
3. We do not provide link to report page for user. I think we could use ShareableLink functionality for this.
4. We can calculate dependency score and send it right in check description (it will be shown in pull request at github). Right now its calculated on frontend (if I remember correctly), so we will need to calculate it in backend too (or calculate only in backend, then send to frontend).

# Deployment Guide: Hosting on Render

This guide will help you deploy your **Insurance Extraction App** to the web using **Render**, a cloud provider that offers a generous free tier and is very easy to use.

## Prerequisites

1.  **GitHub Account**: You need to push your code to a GitHub repository.
2.  **Render Account**: Sign up at [render.com](https://render.com) (you can sign up with GitHub).
3.  **Gemini API Key**: Your `GEMINI_API_KEY` from your `.env` file.

## Step 1: Push Code to GitHub

Since you are running this locally, you need to push your code to a new GitHub repository.
1.  Initialize git if you haven't: `git init`
2.  Add files: `git add .`
3.  Commit: `git commit -m "Initial commit"`
4.  Create a new repository on GitHub.
5.  Link and push your code:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    git push -u origin master
    ```

## Step 2: Create a Web Service on Render

1.  Log in to your [Render Dashboard](https://dashboard.render.com/).
2.  Click the **New +** button and select **Web Service**.
3.  Select **Build and deploy from a Git repository**.
4.  Connect your GitHub account and select the repository you just created.

## Step 3: Configure the Service

Render will detect the `Dockerfile` we created. Use the following settings:

-   **Name**: `insurance-extractor` (or any name you like)
-   **Region**: Choose the one closest to you (e.g., Oregon, Frankfurt, Singapore).
-   **Branch**: `master` (or `main`)
-   **Runtime**: **Docker** (Render should select this automatically because of the Dockerfile).
-   **Instance Type**: **Free**

## Step 4: Environment Variables (Critical!)

Scroll down to the **Environment Variables** section. You **MUST** add your API key here, or the app will not work.

1.  Click **Add Environment Variable**.
2.  **Key**: `GROQ_API_KEY`
3.  **Value**: (Paste your actual API key here, starting with `gsk_...`)

**Note**: Do NOT upload your `.env` file to GitHub. It is ignored by `.dockerignore` for security. Setting it in the dashboard is the secure way.

## Step 5: Deploy

1.  Click **Create Web Service**.
2.  Render will start building your Docker image. This might take a few minutes.
3.  Watch the logs. You should eventually see: `Uvicorn running on http://0.0.0.0:8000`.

## Step 6: Access Your App

Once the deployment is live, you will see a URL at the top of the dashboard, something like:
`https://insurance-extractor.onrender.com`

**Click it!** Your app is now live on the internet and can be accessed from any browser, anywhere.

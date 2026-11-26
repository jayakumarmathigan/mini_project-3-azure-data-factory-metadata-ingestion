# Setup guide

**Cost:** these Azure resources can be billed, including pipeline runs, copy activity,
debug runs and storage. Check your subscription, credits and current pricing, and set a
budget alert (an alert does not stop spending).

## Part A: Upload to GitHub
Create a **public**, empty repository named `azure-data-factory-metadata-ingestion`
(no README, .gitignore or license). Unzip the project, open a terminal inside it and run:
```bash
git init
git add .
git commit -m "Add metadata-driven ADF ingestion project"
git branch -M main
git remote add origin https://github.com/<your-username>/azure-data-factory-metadata-ingestion.git
git push -u origin main
```
Check that the **CI** run in the Actions tab passes.

## Part B: Create Azure resources
Needs the Azure CLI and permission to create role assignments.
Run from the project folder (or use Azure Cloud Shell after cloning your repository).
```bash
az login
az group create --name rg-adf-portfolio --location centralindia
az deployment group create --resource-group rg-adf-portfolio --template-file infra/main.bicep --query properties.outputs
```
Note the storage account and factory names in the output.

Without the CLI, create these in the Azure portal:
1. A storage account with **hierarchical namespace** enabled
2. Containers `source`, `bronze` and `config`
3. A Data Factory (V2), which has a system-assigned managed identity by default
4. On the storage account, **Access control (IAM)**: give the factory's identity the
   **Storage Blob Data Contributor** role. New role assignments can take a few minutes.

## Part C: Upload files
In the portal's storage browser:
- `data/sample/customers.csv`, `products.csv`, `orders.csv` go in the root of `source`
- `config/ingestion_config.json` goes in the root of `config`

If access is denied, your own user may need a Storage Blob Data role too.

## Part D: Connect the factory to GitHub
1. In ADF Studio, open **Manage > Git configuration > Configure**. Choose **GitHub**.
2. Select your repository with:
   - Collaboration branch: `main`
   - Publish branch: `adf_publish`
   - Root folder: `/adf`
   - **Clear** "Import existing resources to repository"
3. Create or choose a working branch, for example `dev`, so changes do not go straight to `main`.
4. In **Manage > Linked services > ls_adls**, replace `<storageaccount>` in the URL with
   your account name. Choose system-assigned managed identity, **Test connection**, save.
   - If the UI does not accept the edit, change `adf/linkedService/ls_adls.json`
     in your working branch and refresh ADF Studio.
5. Open the pipelines and run **Validate all**.

Your storage account name will be visible in your public repository. It is not a
password, but never commit keys, SAS tokens or connection strings.

## Part E: Run and test
1. Open `pl_master_ingestion`, select **Debug** and leave `runDate` empty.
2. In the output, confirm three child runs succeeded and `returns` was skipped.
3. Check the three Parquet files in `bronze`. In each copy activity's output,
   compare `rowsRead` and `rowsCopied` with the README.
4. **Missing file test:** in `config`, set `returns` to `"enabled": true`, upload the edited control file (there is no returns.csv)
   and debug again. Expect the returns run to fail with `SOURCE_FILE_MISSING` while the
   other entities load. The master run should show as failed.
5. Upload the original control file again.

## Part F: Save your work and publish
1. Create a pull request from your working branch to `main`, then merge it.
2. Switch to `main` in ADF Studio and select **Publish**. This deploys to the factory.
3. The trigger stays stopped. To try it, set a future start time, start it in your working
   branch, merge and publish. Stop it again the same way afterwards.

## Part G: Add proof of your run
Add screenshots to `docs/images`: the pipeline canvas, a successful run, the missing-file
failure and the Bronze folders. Hide your email, subscription and tenant IDs.
Link them in the README, commit and push.

## Clean up
When finished, check that the group holds only this project. This **permanently deletes
everything in it**:
```bash
az group delete --name rg-adf-portfolio
```
Your code stays in GitHub.

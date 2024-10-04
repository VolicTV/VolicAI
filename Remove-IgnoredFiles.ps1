# Check if .gitignore exists
if (-not (Test-Path .gitignore)) {
    Write-Error "Error: .gitignore file not found."
    exit 1
}

# Remove files from Git tracking
Write-Host "Removing files listed in .gitignore from Git tracking..."

# Read .gitignore and process each line
Get-Content .gitignore | ForEach-Object {
    $line = $_.Trim()
    # Ignore empty lines and comments
    if ($line -and -not $line.StartsWith("#")) {
        # Remove the file/directory from Git tracking
        $output = git rm -r --cached $line 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Removed from tracking: $line"
        } else {
            Write-Host "Not tracked or doesn't exist: $line"
        }
    }
}

# Commit the changes
Write-Host "Committing changes..."
git add .gitignore
git commit -m "Remove files listed in .gitignore from tracking"

# Push changes to remote repository
Write-Host "Pushing changes to remote repository..."
git push origin main  # Change 'main' to your branch name if different

Write-Host "Operation completed."
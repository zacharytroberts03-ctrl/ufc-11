$action  = New-ScheduledTaskAction -Execute "c:\Users\Owner\Desktop\Claude\run_card_deals.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "CardDealsUpdater" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Done. Task CardDealsUpdater created - runs daily at 12pm."

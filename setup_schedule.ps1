$action = New-ScheduledTaskAction -Execute "c:\Users\Owner\Desktop\Claude\run_card_deals.bat"

$triggers = @(
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday    -At "9:00AM"
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At "2:00PM"
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday    -At "8:00PM"
)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName "CardDealsUpdater" -Action $action -Trigger $triggers -Settings $settings -Force
Write-Host "Done. CardDealsUpdater runs Mon 9am, Wed 2pm, Fri 8pm (wakes laptop, runs on battery, catches up if missed)."

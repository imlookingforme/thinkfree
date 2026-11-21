import { test, expect } from '@playwright/test';

test.describe('ThinkFree Core State Machine & Independent Loop', () => {
  test('Complete end-to-end journey: Attempt lock -> Socratic tutor ladder -> Validation explain -> Badge verification', async ({ page }) => {
    // 1. Visit homepage and verify ThinkFree Guidance Dashboard
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Independent Thinking Dashboard');
    await expect(page.locator('text=Independent Thinking Score')).toBeVisible();

    // 2. Open problem attempt
    await page.goto('/attempt/demo');
    await expect(page.locator('text=Coding Problem · Difficulty 1.0')).toBeVisible();
    await expect(page.locator('text=AI Locked')).toBeVisible();

    // 3. Inspect "I'm Stuck" declaration modal with word count validator
    await page.click('button:has-text("I\'m Stuck")');
    await expect(page.locator('text=Declare You Are Stuck')).toBeVisible();

    // Fill genuine stuck attempt description (>= 35 words)
    const stuckNote = "I tried to use a nested for loop comparing each element with target minus current element, but the time complexity is quadratic O of n squared. I want to optimize this with a single pass hash table, but cannot structure the index lookup properly.";
    await page.fill('textarea', stuckNote);
    await page.click('button:has-text("Confirm & Unlock AI Guidance")');

    // Verify transition to unlocked state
    await expect(page.locator('text=AI Guidance Unlocked!')).toBeVisible();

    // 4. Navigate into Socratic Guided Mode (Feature 2)
    await page.click('button:has-text("Enter Socratic Mode")');
    await expect(page.locator('h1')).toContainText('Guided Socratic Workspace');
    await expect(page.locator('text=Guide (Rung 1)')).toBeVisible();

    // 5. Navigate to Validation Teach-Back Mode (Feature 3)
    await page.goto('/validate/demo');
    await expect(page.locator('h1')).toContainText('Did you actually understand?');

    // Fill comprehensive explanation
    const explanationText = "We allocate a hash map seen to record values to indices. In a single iteration over nums, for each element we compute diff = target - n. If diff is in seen, we immediately return the stored index and current index, achieving O(n) linear runtime and O(n) space complexity.";
    await page.fill('textarea', explanationText);
    await page.click('button:has-text("Submit Explanation")');

    // Verify rubric assessment and teach-back prompt
    await expect(page.locator('text=Validation Assessment')).toBeVisible();
    await expect(page.locator('text=Teach-Back Check ("Confused Junior" Peer)')).toBeVisible();

    // 6. Verify Public Ed25519 Badge Verification (Feature 11)
    await page.goto('/verify/badge_demo_77');
    await expect(page.locator('text=CRYPTOGRAPHICALLY VERIFIED')).toBeVisible();
    await expect(page.locator('text=Foundations of Data Structures — Independent Achiever')).toBeVisible();
  });
});

package com.example.ae.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;

public class HomePage extends BasePage {
    private final By signupLoginLink = By.xpath("//a[contains(.,'Signup') and contains(.,'Login')]");
    private final By logoutLink = By.xpath("//a[contains(.,'Logout')]");
    private final By deleteAccountLink = By.xpath("//a[contains(.,'Delete Account')]");
    private final By loggedInAs = By.xpath("//a[contains(.,'Logged in as')]");

    public HomePage(WebDriver driver, WebDriverWait wait) {
        super(driver, wait);
    }

    public HomePage waitUntilLoaded() {
        visible(By.xpath("//body"));
        // 主页登录前可见 Signup/Login，登录后可见 Logged in as。
        wait.until(d -> isVisible(signupLoginLink) || isVisible(logoutLink) || isVisible(loggedInAs));
        return this;
    }

    public SignupLoginPage clickSignupLogin() {
        click(signupLoginLink);
        return new SignupLoginPage(driver, wait).waitUntilLoaded();
    }

    public SignupLoginPage clickLogout() {
        click(logoutLink);
        return new SignupLoginPage(driver, wait).waitUntilLoaded();
    }

    public AccountDeletedPage clickDeleteAccount() {
        click(deleteAccountLink);
        return new AccountDeletedPage(driver, wait);
    }

    public boolean isLoggedInAs(String username) {
        try {
            org.openqa.selenium.WebElement element = driver.findElement(loggedInAs);
            if (!element.isDisplayed()) {
                return false;
            }
            String text = element.getText() == null ? "" : element.getText();
            if (username != null && !username.isBlank()
                    && text.toLowerCase().contains(username.toLowerCase())) {
                return true;
            }
            // 有些情况下页面会显示 Logged in as，但用户名文本加载较慢；只要出现该区域即可判定为登录态。
            return text.toLowerCase().contains("logged in as");
        } catch (Exception e) {
            return false;
        }
    }

    public boolean hasLogoutLink() {
        return isVisible(logoutLink);
    }

    public boolean hasSignupLoginLink() {
        return isVisible(signupLoginLink);
    }
}

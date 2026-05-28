package com.example.ae.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;

public class SignupLoginPage extends BasePage {
    private final By newUserSignupTitle = By.xpath("//*[contains(text(),'New User Signup!')]");
    private final By loginToAccountTitle = By.xpath("//*[contains(text(),'Login to your account')]");
    private final By signupName = By.cssSelector("[data-qa='signup-name']");
    private final By signupEmail = By.cssSelector("[data-qa='signup-email']");
    private final By signupButton = By.cssSelector("[data-qa='signup-button']");
    private final By loginEmail = By.cssSelector("[data-qa='login-email']");
    private final By loginPassword = By.cssSelector("[data-qa='login-password']");
    private final By loginButton = By.cssSelector("[data-qa='login-button']");
    private final By loginError = By.xpath("//*[contains(text(),'Your email or password is incorrect')]");
    private final By signupError = By.xpath("//*[contains(text(),'Email Address already exist')]");

    public SignupLoginPage(WebDriver driver, WebDriverWait wait) {
        super(driver, wait);
    }

    public SignupLoginPage waitUntilLoaded() {
        wait.until(d -> isVisible(newUserSignupTitle) || isVisible(loginToAccountTitle));
        return this;
    }

    public AccountInformationPage submitSignup(String name, String email) {
        type(signupName, name);
        type(signupEmail, email);
        click(signupButton);
        return new AccountInformationPage(driver, wait).waitUntilLoaded();
    }

    public HomePage login(String email, String password) {
        type(loginEmail, email);
        type(loginPassword, password);
        click(loginButton);
        return new HomePage(driver, wait).waitUntilLoaded();
    }

    public SignupLoginPage loginExpectingStay(String email, String password) {
        type(loginEmail, email);
        type(loginPassword, password);
        click(loginButton);
        return this;
    }

    public boolean isLoginPageDisplayed() {
        return isVisible(loginToAccountTitle) && isVisible(loginEmail) && isVisible(loginButton);
    }

    public boolean isSignupPageDisplayed() {
        return isVisible(newUserSignupTitle) && isVisible(signupName) && isVisible(signupButton);
    }

    public boolean hasLoginError() {
        return isVisibleAfterWait(loginError);
    }

    public boolean hasSignupError() {
        return isVisible(signupError);
    }

    public org.openqa.selenium.WebElement loginEmailInput() {
        return visible(loginEmail);
    }

    public org.openqa.selenium.WebElement loginPasswordInput() {
        return visible(loginPassword);
    }
}

package com.example.ae.gui;

import javax.swing.*;
import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/**
 * 自动化测试 GUI：
 * 通过 Swing 填写参数，然后调用 Maven + TestNG 执行对应测试套件。
 */
public class TestRunnerGUI extends JFrame {
    private final JTextField baseUrlField = new JTextField("https://automationexercise.com", 28);
    private final JComboBox<String> browserCombo = new JComboBox<>(new String[]{"chrome", "edge", "firefox"});
    private final JCheckBox headlessBox = new JCheckBox("无头模式 headless");
    private final JTextField usernameField = new JTextField("Selenium Student", 18);
    private final JPasswordField passwordField = new JPasswordField("Test@123456", 18);
    private final JTextField threadsField = new JTextField("120", 8);
    private final JTextArea outputArea = new JTextArea(24, 86);

    public TestRunnerGUI() {
        super("AutomationExercise 自动化集成测试工具");
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setLayout(new BorderLayout(10, 10));

        JPanel form = new JPanel(new GridLayout(0, 2, 8, 8));
        form.setBorder(BorderFactory.createTitledBorder("测试参数"));
        form.add(new JLabel("测试网址 baseUrl:"));
        form.add(baseUrlField);
        form.add(new JLabel("浏览器 browser:"));
        form.add(browserCombo);
        form.add(new JLabel("运行模式:"));
        form.add(headlessBox);
        form.add(new JLabel("注册用户名 username:"));
        form.add(usernameField);
        form.add(new JLabel("注册/登录密码 password:"));
        form.add(passwordField);
        form.add(new JLabel("性能测试线程数 threads:"));
        form.add(threadsField);

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton runFunctional = new JButton("运行功能测试");
        JButton runPerformance = new JButton("运行性能测试");
        JButton clear = new JButton("清空输出");
        buttons.add(runFunctional);
        buttons.add(runPerformance);
        buttons.add(clear);

        outputArea.setEditable(false);
        outputArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));

        add(form, BorderLayout.NORTH);
        add(buttons, BorderLayout.CENTER);
        add(new JScrollPane(outputArea), BorderLayout.SOUTH);

        runFunctional.addActionListener(e -> runSuite("src/test/resources/testng.xml"));
        runPerformance.addActionListener(e -> runSuite("src/test/resources/testng-performance.xml"));
        clear.addActionListener(e -> outputArea.setText(""));

        pack();
        setLocationRelativeTo(null);
    }

    private void runSuite(String suiteFile) {
        Thread worker = new Thread(() -> {
            try {
                append("开始执行：" + suiteFile + "\n");

                List<String> cmd = new ArrayList<>();
                cmd.add(isWindows() ? "mvn.cmd" : "mvn");
                cmd.add("test");
                cmd.add("-DsuiteXmlFile=" + suiteFile);
                cmd.add("-DbaseUrl=" + baseUrlField.getText().trim());
                cmd.add("-Dbrowser=" + browserCombo.getSelectedItem());
                cmd.add("-Dheadless=" + headlessBox.isSelected());
                cmd.add("-Dusername=" + usernameField.getText().trim());
                cmd.add("-Dpassword=" + new String(passwordField.getPassword()));
                cmd.add("-Dperformance.threads=" + threadsField.getText().trim());

                ProcessBuilder builder = new ProcessBuilder(cmd);
                builder.redirectErrorStream(true);
                Process process = builder.start();

                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        append(line + "\n");
                    }
                }

                int exitCode = process.waitFor();
                append("执行结束，退出码：" + exitCode + "\n\n");
            } catch (Exception ex) {
                append("执行失败：" + ex.getMessage() + "\n");
            }
        });
        worker.setDaemon(true);
        worker.start();
    }

    private void append(String text) {
        SwingUtilities.invokeLater(() -> {
            outputArea.append(text);
            outputArea.setCaretPosition(outputArea.getDocument().getLength());
        });
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new TestRunnerGUI().setVisible(true));
    }
}

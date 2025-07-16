# Multi-agent cold email generator + evaluator
* ``openai_sales_agent/app.py``
 => simple Agent system for generating cold sales 

 * ``openai_sales_agent/using_tools/app.py``
 => simple Agent system for generating cold sales using Tools and Handoffs to call functions

<br>
```
           +--------------------+
           |   Sales Manager    |
           |   (Top-level Agent)| 
           +--------+-----------+
                    |
        +-----------+-----------+--------------------+
        |           |           |                    |
   tool:agent1  tool:agent2  tool:agent3         handoff:
                                        +------------------------+
                                        |   Email Manager Agent  |
                                        +------------------------+
                                        | subject_writer (tool)  |
                                        | html_converter (tool)  |
                                        | send_html_email (tool) |
                                        +------------------------+

```
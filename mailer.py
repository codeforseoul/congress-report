import mandrill
mandrill_client = mandrill.Mandrill('ykwn-gyhVLeYCgcXMMNvfQ');

template_name = 'test_for_congress_report'
template_content = [{'content': 'example content', 'name': 'example name'}]

message = {
  'from_email': 'thechunsik@gmail.com',
  'from_name': 'Hoony, Jang',
  'subject': 'test email',
  'to': [{
    'email': 'thechunsik@gmail.com',
    'name': 'Hoony, Jang',
    'type': 'to'
  }],
  "global_merge_vars": [{
    "name": "user_name",
    "content": "Hoony, Jang"
  }]
}

result = mandrill_client.messages.send_template(template_name = template_name, template_content = template_content, message = message, async = False)
print(result)

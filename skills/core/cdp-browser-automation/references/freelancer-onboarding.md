# Freelancer Onboarding Flow (Angular 19)

## Páginas do onboarding (ordem)

1. `/new-freelancer/skills` — Selecionar categoria + skills
2. `/new-freelancer/linked-accounts` — Skip
3. `/new-freelancer/profile-details/photo-and-name` — Preencher nome
4. `/new-freelancer/profile-details/headline-and-summary` — Preencher headline (≤50 chars) + summary
5. `/new-freelancer/profile-details/languages-and-birthdate` — Preencher idioma + data nascimento
6. `/new-freelancer/payment-verification` — Skip
7. `/new-freelancer/membership-offer` — Skip (botão é `<a>`)
8. `/new-freelancer/experiences` — Skip
9. `/new-freelancer/references` — Finish → `/search/projects`

## Estrutura DOM Angular

### Lista de skills
```
<fl-list-item>
  <div class="BitsListItemHeader OuterPadding HasHoverState">
    <div class="BitsListItemContent">
      <div class="SkillsContent-details">
        <p class="SkillsContent-text"> Python  (262 jobs) </p>
        <fl-icon data-name="ui-plus">...</fl-icon>
      </div>
    </div>
  </div>
</fl-list-item>
```
Clicar no `.BitsListItemHeader` seleciona a skill.

### Inputs Angular
- `fl-input` → input nativo: `fl-input .NativeElement`
- `fl-textarea` → textarea nativo: `textarea.TextArea`

### Placeholders
- Headline: `e.g. Data Scientist`
- Summary: `Describe your top skills, strengths, and experiences...`
- Nome: `Enter your first name` / `Enter your last name`
- Nascimento: `input#inputBirthdate` placeholder `MM/DD/YYYY`
- Idioma: campo de autocomplete (`input`), digitar e pressionar Enter

## Validações

- Headline: **máximo 50 caracteres**
- Summary: máximo 3000 caracteres
- Birthdate: formato MM/DD/YYYY (pelo menos 16 anos)
- Languages: selecionar ao menos 1 (digitar + Enter no autocomplete)

## Técnica de input

`Input.dispatchKeyEvent` caractere por caractere:
```python
for char in text:
    cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'text': char, 'key': char})
    cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'text': char, 'key': char})
```

Triple-click para selecionar texto existente antes de digitar:
```python
cdp('Input.dispatchMouseEvent', {..., 'clickCount': 3})
```

## Skills recomendadas (máximo 20)

Python, Automation, Web Scraping, API Development, API Integration, Data Collection, Linux, JavaScript, Node.js, Data Management, Website Optimization, Cloud Computing, Google Sheets, Analytics, Documentation

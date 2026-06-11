-- Pandoc Lua filter for the resume LaTeX -> Markdown export.
-- Works on the document produced via scripts/pandoc-defs.tex:
--  * \name/\address arrive as title/author metadata; they are turned
--    back into an H1 plus contact-line paragraphs at the top.
--  * each rSubsection arrives as an H3 followed by a blockquote holding
--    "dates|role|location"; that becomes a single italic line, dropping
--    whichever fields are empty.
--  * the $\cdot$ separators in the contact line become a literal ".".

local stringify = pandoc.utils.stringify

local function meta_line(quote)
  local parts = {}
  for field in (stringify(quote) .. "|"):gmatch("(.-)|") do
    field = field:gsub("^%s+", ""):gsub("%s+$", "")
    if field ~= "" then table.insert(parts, field) end
  end
  if #parts == 0 then return nil end
  return pandoc.Para({ pandoc.Emph(pandoc.Inlines(table.concat(parts, " \u{00b7} "))) })
end

function Math(m)
  if m.text:match("^%s*\\cdot%s*$") then
    return pandoc.Str("\u{00b7}")
  end
end

function Pandoc(doc)
  local blocks = pandoc.Blocks({})
  if doc.meta.title then
    blocks:insert(pandoc.Header(1, pandoc.Inlines(doc.meta.title)))
    doc.meta.title = nil
  end
  for _, addr in ipairs(doc.meta.author or {}) do
    blocks:insert(pandoc.Para(pandoc.Inlines(addr)))
  end
  doc.meta.author = nil
  local prev_was_h3 = false
  for _, block in ipairs(doc.blocks) do
    if prev_was_h3 and block.t == "BlockQuote" then
      local line = meta_line(block)
      if line then blocks:insert(line) end
    else
      blocks:insert(block)
    end
    prev_was_h3 = (block.t == "Header" and block.level == 3)
  end
  doc.blocks = blocks
  return doc
end

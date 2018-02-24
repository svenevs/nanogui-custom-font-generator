# `rake`: in same directory as this file: compiles the fonts
# `rake clean`: removes the compiled files from compiled_fonts
namespace :customfont do
    task :compile do
        puts "Compiling icons..."
        puts %x(fontcustom compile)
    end
end

task :default => 'customfont:compile'

task :clean do
    puts "Removing generated fonts / css / testing site from compild_fonts/"
    FileUtils.rm_rf(Dir.glob('compiled_fonts/*'))
    puts "Deleting fontcustom manifest"
    FileUtils.rm_rf(".fontcustom-manifest.json")
end
